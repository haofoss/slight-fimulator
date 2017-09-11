#!/usr/cin/env python
# -*- coding:utf-8 -*-

"""The code for importing the package.

Unofficial Utilities for Pygame - An unofficial module that makes Pygame coding easier.
Copyright (C) 2017 Adrien Hopkins

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""

from __future__ import absolute_import

if __name__ == '__main__':
    import game
    import sprite
else:
    from . import game, sprite
    
__author__ = "Adrien Hopkins"
__version__ = "3.0.1"

Game = game.Game
BG_PRESETS = Game.BG_PRESETS
ImprovedSprite = sprite.ImprovedSprite
RectSprite = sprite.RectSprite
Button = sprite.Button
