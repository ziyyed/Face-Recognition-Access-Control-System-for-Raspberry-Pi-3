"""
LCD helper for Raspberry Pi 3 access-control demo.

Uses an I2C 16x2 display via the RPLCD library when available.
Falls back to a console-only mock so the script can be developed
on non-Pi machines (e.g., Windows laptop running Proteus).
"""

from __future__ import annotations

import contextlib
import logging
import time
from typing import Optional

try:
    from RPLCD.i2c import CharLCD  # type: ignore
except Exception:  # pragma: no cover - dev boxes often lack RPLCD
    CharLCD = None  # type: ignore


LCD_I2C_ADDRESS = 0x27  # Common PCF8574 backpacks; adjust if needed.
LCD_COLUMNS = 16
LCD_ROWS = 2
LCD_INIT_MESSAGE = ("Systeme Pret", "")

_LOGGER = logging.getLogger(__name__)


class BaseLCD:
    """Minimal interface used by the main application."""

    def show_message(self, line1: str, line2: str = "") -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class MockLCD(BaseLCD):
    """Fallback when RPLCD or hardware is not available."""

    def show_message(self, line1: str, line2: str = "") -> None:
        print(f"[LCD] {line1} | {line2}")

    def clear(self) -> None:
        print("[LCD] clear")

    def close(self) -> None:
        print("[LCD] close")


class I2CLCD(BaseLCD):
    """Real I2C implementation."""

    def __init__(self) -> None:
        if CharLCD is None:
            raise RuntimeError("RPLCD not installed")
        self._lcd = CharLCD(
            i2c_expander="PCF8574",
            address=LCD_I2C_ADDRESS,
            cols=LCD_COLUMNS,
            rows=LCD_ROWS,
            charmap="A02",
            auto_linebreaks=False,
        )

    def show_message(self, line1: str, line2: str = "") -> None:
        self._lcd.clear()
        self._lcd.write_string(f"{line1[:LCD_COLUMNS]:<{LCD_COLUMNS}}")
        self._lcd.cursor_pos = (1, 0)
        self._lcd.write_string(f"{line2[:LCD_COLUMNS]:<{LCD_COLUMNS}}")

    def clear(self) -> None:
        self._lcd.clear()

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self._lcd.close(clear=True)


def init_lcd(force_mock: bool = False) -> BaseLCD:
    """
    Create an LCD instance.

    Parameters
    ----------
    force_mock: Force console mock (useful for Proteus-only tests on PC)
    """

    if force_mock or CharLCD is None:
        _LOGGER.warning("Using Mock LCD (no RPLCD or force_mock=True)")
        lcd: BaseLCD = MockLCD()
    else:
        lcd = I2CLCD()

    line1, line2 = LCD_INIT_MESSAGE
    lcd.show_message(line1, line2)
    time.sleep(1)
    return lcd


def show_message(lcd: Optional[BaseLCD], line1: str, line2: str = "") -> None:
    if lcd is None:
        return
    lcd.show_message(line1, line2)


def clear_lcd(lcd: Optional[BaseLCD]) -> None:
    if lcd is None:
        return
    lcd.clear()


