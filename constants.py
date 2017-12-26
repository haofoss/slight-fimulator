#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""All of the constants for the game.

Slight Fimulator - Flight simulator in Python
Copyright (C) 2017 Hao Tian and Adrien Hopkins
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Installs Python 3 division and print behaviour
from __future__ import division, print_function

import os

PATH = os.path.dirname(os.path.realpath(__file__))
LOG_PATH = None
# Uncomment this line to save logs to disk
#LOG_PATH = os.path.join(PATH, "logs")

UNITS = (
    {
        'name': "SI",
        'speed': {
            'name': "M/S",
            'value': 1,
            'round-to': 1
        },
        'pos': {
            'name': "M",
            'value': 1,
            'round-to': 0
        }
    },
    {
        'name': "Metric",
        'speed': {
            'name': "KM/H",
            'value': 3.6,
            'round-to': 0
        },
        'pos': {
            'name': "KM",
            'value': .001,
            'round-to': 3
        }
    },
    {
        'name': "Imperial",
        'speed': {
            'name': "FT/S",
            'value': 1 / 0.3048,
            'round-to': 0
        },
        'pos': {
            'name': "FT",
            'value': 1 / 0.3048,
            'round-to': 0
        }
    }
)

AIRSPACE_DIM = 100000

MIN_OBJ_ALT = 7500
MAX_ALTITUDE = 20000
ALTITUDE_TOLERANCE = 1400
ALTITUDE_WITHIN = 2000
POINTS_REQUIRED = 10

