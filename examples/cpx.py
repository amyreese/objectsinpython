# Copyright 2019 John Reese
# Licensed under the MIT license

"""
Example controller using a Circuit Playground Express.

Neopixels show boolean values:

Button A triggers undock.
"""

import board
import neopixel
from oip import OIP

OFF = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

pixels = neopixel.NeoPixel(board.NEOPIXEL, 10, brightness=0.02, auto_write=True)
pixels.fill(OFF)
pixels.show()

oip = OIP()


@oip.on("IFF_ACTIVE")
def iff_active(now, value):
    pixels[0] = GREEN if value else RED


@oip.press(board.BUTTON_B)
def button_b(now, value):
    if value:
        oip.execute("UNDOCK")


@oip.press(board.BUTTON_A)
def button_a(now, value):
    pixels[9] = GREEN if value else RED
    oip.execute("BURN_MAIN_ENGINE" if value else "STOP_MAIN_ENGINE")


@oip.press(board.A5, touch=True)
def turn_left(now, value):
    oip.execute("FIRE_RCS_CCW" if value else "STOP_RCS")


@oip.press(board.A6, touch=True)
def turn_right(now, value):
    oip.execute("FIRE_RCS_CW" if value else "STOP_RCS")


oip.start()
