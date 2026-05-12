"""Helpers for building OpenOCD commands for Renesas RA devices."""

from __future__ import annotations

import shlex
from typing import Iterable


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
