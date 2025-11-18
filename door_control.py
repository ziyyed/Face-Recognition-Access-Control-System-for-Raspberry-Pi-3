"""
Simple motor / door lock controller using RPi.GPIO.

The module exposes a class so we can mock it easily when testing on
non-Raspberry Pi hardware (e.g., Windows + Proteus simulation).
"""

from __future__ import annotations

import logging
import time
from typing import Optional

try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:  # pragma: no cover - dev boxes lack GPIO
    GPIO = None  # type: ignore

_LOGGER = logging.getLogger(__name__)

# === Configuration (BCM pin numbering) ===
MOTOR_PIN = 18
MOTOR_ACTIVE_STATE = GPIO.HIGH if GPIO else 1  # type: ignore
MOTOR_INACTIVE_STATE = GPIO.LOW if GPIO else 0  # type: ignore
DEFAULT_OPEN_DURATION = 5.0  # seconds the door stays open


class BaseDoorController:
    def open_door(self, duration_seconds: float = DEFAULT_OPEN_DURATION) -> None:
        raise NotImplementedError

    def close_door(self) -> None:
        raise NotImplementedError

    def cleanup(self) -> None:
        raise NotImplementedError


class GPIODoorController(BaseDoorController):
    def __init__(self) -> None:
        if GPIO is None:
            raise RuntimeError("RPi.GPIO not available")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(MOTOR_PIN, GPIO.OUT, initial=MOTOR_INACTIVE_STATE)

    def open_door(self, duration_seconds: float = DEFAULT_OPEN_DURATION) -> None:
        _LOGGER.info("Opening door for %.1f s", duration_seconds)
        GPIO.output(MOTOR_PIN, MOTOR_ACTIVE_STATE)
        time.sleep(duration_seconds)
        GPIO.output(MOTOR_PIN, MOTOR_INACTIVE_STATE)

    def close_door(self) -> None:
        _LOGGER.info("Closing door")
        GPIO.output(MOTOR_PIN, MOTOR_INACTIVE_STATE)

    def cleanup(self) -> None:
        with suppress_gpio_warning():
            GPIO.output(MOTOR_PIN, MOTOR_INACTIVE_STATE)
            GPIO.cleanup()


class MockDoorController(BaseDoorController):
    def open_door(self, duration_seconds: float = DEFAULT_OPEN_DURATION) -> None:
        print(f"[DOOR] open for {duration_seconds}s")
        time.sleep(min(duration_seconds, 0.1))

    def close_door(self) -> None:
        print("[DOOR] close")

    def cleanup(self) -> None:
        print("[DOOR] cleanup")


class suppress_gpio_warning:
    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def init_door_controller(force_mock: bool = False) -> BaseDoorController:
    if force_mock or GPIO is None:
        _LOGGER.warning("Using Mock door controller (no RPi.GPIO or force_mock=True)")
        controller: BaseDoorController = MockDoorController()
    else:
        controller = GPIODoorController()
    controller.close_door()
    return controller


def open_door(controller: Optional[BaseDoorController], duration_seconds: float = DEFAULT_OPEN_DURATION) -> None:
    if controller is None:
        return
    controller.open_door(duration_seconds)


def close_door(controller: Optional[BaseDoorController]) -> None:
    if controller is None:
        return
    controller.close_door()


