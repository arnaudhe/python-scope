# python-scope
Graphical scope from serial or socket data using python. The settings are based on a json file.

<img src="https://raw.githubusercontent.com/arnaudhe/python-scope/master/img/screenshot.png" width="500">

## Dependancies

* numpy
* json
* pyserial
* pygame

`sudo pip install numpy pyserial pygame`

## Usage

`python scope.py <conf_file_json>`

## Test

`python test/udp_triangle.py`
`python scope.py test/conf_udp_triangle.json`
