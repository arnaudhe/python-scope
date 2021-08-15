# python-scope
Graphical scope from serial or socket data using python. The settings are based on a json file.

<img src="https://raw.githubusercontent.com/arnaudhe/python-scope/master/img/screenshot.png" width="500">

## Dependencies

* numpy
* json
* pyserial
* pygame

`pip install -r requirements.txt`

## Usage (script)

`python scope.py <conf_file_json>`

## Usage (package)

```python
import pygame
from scope.scope import Oscilloscope, DataReaderUdp

UDP_PORT = 8000
CHANNELS = 4
WIDTH = 1280
HEIGHT = 1080
DEPTH = 200
MIN = -10.0
MAX = 10.0

pygame.init()
reader = DataReaderUdp(UDP_PORT, CHANNELS, r"(.+)", DEPTH)
scope = Oscilloscope(reader, CHANNELS, WIDTH, HEIGHT, DEPTH, MIN, MAX, ["channel 1", "channel 2", "channel 3", "channel 4"])
```

## Test

`python scope.py test/udp_triangle.py`
`python scope.py test/conf_udp_triangle.json`
