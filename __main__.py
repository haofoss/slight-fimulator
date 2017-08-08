#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""Runs the package."""

import game

screen_size = (1280, 960)

if __name__ == '__main__':
    window = game.GameWindow(size=screen_size)
    window.mainloop()
