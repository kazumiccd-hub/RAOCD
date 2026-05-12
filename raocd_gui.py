"""CustomTkinter GUI for writing Renesas RA firmware with OpenOCD."""

from __future__ import annotations

import queue
import shlex
import subprocess
import threading
from pathlib import Path
from typing import Iterable

import customtkinter as ctk
from tkinter import filedialog


INTERFACE_CONFIG = "interface/cmsis-dap.cfg"
TARGET_CONFIG = "target/renesas_ra.cfg"


def quote_openocd_path(path: str) -> str:
    """Quote a file path for use inside an OpenOCD command argument."""
    return '"' + path.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_openocd_command(openocd_path: str, binary_path: str) -> list[str]:
    """Build the OpenOCD command used by the Write button."""
    executable = openocd_path.strip() or "openocd"
    program_command = f"program {quote_openocd_path(binary_path)} verify reset exit"
    return [
        executable,
        "-f",
        INTERFACE_CONFIG,
        "-f",
        TARGET_CONFIG,
        "-c",
        program_command,
    ]


def command_for_display(command: Iterable[str]) -> str:
    """Return a shell-like command string for the log area."""
    return " ".join(shlex.quote(part) for part in command)


class RAOpenOCDApp(ctk.CTk):
    """OpenOCD writer GUI for Renesas RA series devices."""

    def __init__(self) -> None:
        super().__init__()

        self.title("Renesas RA OpenOCD Writer")
        self.geometry("780x520")
        self.minsize(720, 460)

        self.openocd_path = ctk.StringVar(value="openocd")
        self.binary_path = ctk.StringVar()
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.worker_thread: threading.Thread | None = None

        self._build_widgets()
        self.after(100, self._poll_log_queue)

    def _build_widgets(self) -> None:
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        form_frame = ctk.CTkFrame(self)
        form_frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        form_frame.grid_columnconfigure(1, weight=1)

        openocd_label = ctk.CTkLabel(form_frame, text="OpenOCD Path")
        openocd_label.grid(row=0, column=0, padx=(12, 8), pady=12, sticky="w")

        openocd_entry = ctk.CTkEntry(form_frame, textvariable=self.openocd_path)
        openocd_entry.grid(row=0, column=1, padx=8, pady=12, sticky="ew")

        openocd_button = ctk.CTkButton(
            form_frame,
            text="Browse...",
            width=110,
            command=self._select_openocd,
        )
        openocd_button.grid(row=0, column=2, padx=(8, 12), pady=12)

        binary_label = ctk.CTkLabel(form_frame, text="Binary File")
        binary_label.grid(row=1, column=0, padx=(12, 8), pady=(0, 12), sticky="w")

        binary_entry = ctk.CTkEntry(form_frame, textvariable=self.binary_path)
        binary_entry.grid(row=1, column=1, padx=8, pady=(0, 12), sticky="ew")

        binary_button = ctk.CTkButton(
            form_frame,
            text="Browse...",
            width=110,
            command=self._select_binary,
        )
        binary_button.grid(row=1, column=2, padx=(8, 12), pady=(0, 12))

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)

        self.write_button = ctk.CTkButton(
            action_frame,
            text="Write",
            width=140,
            height=40,
            command=self._start_write,
        )
        self.write_button.grid(row=0, column=1, sticky="e")

        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=2, column=0, padx=16, pady=(8, 16), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        log_label = ctk.CTkLabel(log_frame, text="Execution Log")
        log_label.grid(row=0, column=0, padx=12, pady=(12, 4), sticky="w")

        self.log_text = ctk.CTkTextbox(log_frame, wrap="word")
        self.log_text.grid(row=1, column=0, padx=12, pady=(4, 12), sticky="nsew")

    def _select_openocd(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select OpenOCD executable",
            filetypes=(("OpenOCD executable", "openocd*"), ("All files", "*.*")),
        )
        if selected:
            self.openocd_path.set(selected)

    def _select_binary(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select firmware file",
            filetypes=(
                ("Firmware files", "*.hex *.bin *.elf *.srec *.mot"),
                ("HEX files", "*.hex"),
                ("All files", "*.*"),
            ),
        )
        if selected:
            self.binary_path.set(selected)

    def _start_write(self) -> None:
        binary_path = self.binary_path.get().strip()
        if not binary_path:
            self._append_log("Please select a binary file.\n")
            return

        if not Path(binary_path).is_file():
            self._append_log(f"Binary file does not exist: {binary_path}\n")
            return

        command = build_openocd_command(self.openocd_path.get(), binary_path)
        self._append_log("\n$ " + command_for_display(command) + "\n")
        self.write_button.configure(state="disabled")

        self.worker_thread = threading.Thread(
            target=self._run_openocd,
            args=(command,),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_openocd(self, command: list[str]) -> None:
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            self.log_queue.put(f"Failed to start OpenOCD: {exc}\n")
            self.log_queue.put("__WRITE_DONE__")
            return

        assert process.stdout is not None
        for line in process.stdout:
            self.log_queue.put(line)

        return_code = process.wait()
        self.log_queue.put(f"\nOpenOCD exited with code {return_code}.\n")
        self.log_queue.put("__WRITE_DONE__")

    def _poll_log_queue(self) -> None:
        while True:
            try:
                message = self.log_queue.get_nowait()
            except queue.Empty:
                break

            if message == "__WRITE_DONE__":
                self.write_button.configure(state="normal")
            else:
                self._append_log(message)

        self.after(100, self._poll_log_queue)

    def _append_log(self, message: str) -> None:
        self.log_text.insert("end", message)
        self.log_text.see("end")


def main() -> None:
    app = RAOpenOCDApp()
    app.mainloop()


if __name__ == "__main__":
    main()
