#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""Runs the package.

Slight Fimulator - Flight simlator in Python
Copyright (C) 2017 Hao Tian
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

ALTERNATE NAMES
Glide Slope
Departure As Filed
Hundred Above
Decision Height
Dank Angle
Dlight simulator
SLOGAN
Just a bit of fimulating"""

import game

screen_size = (1280, 960)

if __name__ == '__main__':
    window = game.Game(size=screen_size)
    window.mainloop()
