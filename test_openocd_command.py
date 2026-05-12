"""Tests for OpenOCD command construction."""

import unittest

from openocd_command import build_openocd_command


class OpenOCDCommandTest(unittest.TestCase):
    def test_build_openocd_command_uses_renesas_ra_configs(self) -> None:
        command = build_openocd_command("openocd", "firmware.hex")

        self.assertEqual(
            command,
            [
                "openocd",
                "-f",
                "interface/cmsis-dap.cfg",
                "-f",
                "target/renesas_ra.cfg",
                "-c",
                'program "firmware.hex" verify reset exit',
            ],
        )

    def test_build_openocd_command_defaults_to_openocd(self) -> None:
        command = build_openocd_command("", "firmware.hex")

        self.assertEqual(command[0], "openocd")


if __name__ == "__main__":
    unittest.main()
