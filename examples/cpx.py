# Copyright 2019 John Reese
# Licensed under the MIT license

"""
Example controller using a Circuit Playground Express.

Neopixels show boolean values:

Button A triggers undock.
"""

import board
import neopixel
from cpgame import on
from oip import OIP, Boolean

OFF = (0, 0, 0)
GREEN = (0, 0, 255)
RED = (255, 0, 0)

pixels = neopixel.NeoPixel(board.NEOPIXEL, 10, brightness=0.02, auto_write=True)
pixels.fill(OFF)
pixels.show()


oip = OIP()


@oip.on(Boolean.IFF_ACTIVE)
def iff_active(now, value):
    pixels[0] = GREEN if value else RED


oip.start()
