Objects In Python
=================

Interface to [Objects In Space][ois] for [CircuitPython][] embedded hardware.

[![build status](https://travis-ci.org/jreese/objectsinpython.svg?branch=master)](https://travis-ci.org/jreese/objectsinpython)
[![version](https://img.shields.io/pypi/v/objectsinpython.svg)](https://pypi.org/project/objectsinpython)
[![license](https://img.shields.io/pypi/l/objectsinpython.svg)](https://github.com/jreese/objectsinpython/blob/master/LICENSE)
[![code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


Install
-------

Download the [compiled module][builds] and copy them to your board. Note there are two
versions: "full" or regular for boards with more memory (eg, M4/samd51) and "tiny" for
boards with less memory (eg, M0/samd21). When using the tiny build, be sure to rename
the module to `oip.mpy`.

```bash
$ cp -X oip.mpy /Volumes/CIRCUITPY/oip.mpy
```

OR

```bash
$ cp -X oip-tiny.mpy /Volumes/CIRCUITPY/oip.mpy
```


Overview
--------

Objects In Python uses a simple, event-based API to execute your functions when buttons
are pressed or game values update. Getting started is as easy as importing the module,
creating the interface, and starting the connection:

```python
from oip import OIP

oip = OIP()
...
oip.start()
```

Turn lights on or off when game state changes: 

```python
@oip.on("IFF_ACTIVE")
def iff_active(now, value):
    pixels[0] = BLUE if value else RED
```

Connect buttons to game commands:

```python
@oip.press(board.BUTTON_A)
def thrust_while_holding(now, value):
    oip.execute("BURN_MAIN_ENGINE" if value else "STOP_MAIN_ENGINE")
```

With the full build, use helper classes to mitigate typoes:

```python
@oip.on(Boolean.IFF_ACTIVE)
def iff_active(now, value):
    ...

@oip.press(board.BUTTON_A)
def thrust_while_holding(now, value):
    oip.execute(Command.BURN_MAIN_ENGINE if value else Command.STOP_MAIN_ENGINE)
```

Check out the [example projects][examples] for more ideas.


License
-------

Objects In Python is copyright [John Reese](https://jreese.sh), and licensed under the
MIT license.  I am providing code in this repository to you under an open source
license.  This is my personal repository; the license you receive to my code
is from me and not from my employer. See the `LICENSE` file for details.

[ois]: http://objectsgame.com/
[CircuitPython]: https://circuitpython.org
[builds]: https://github.com/jreese/objectsinpython/releases/latest
[examples]: https://github.com/jreese/objectsinpython/tree/master/examples