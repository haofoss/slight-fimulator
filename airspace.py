#!/usr/bin/env python3

"""The Airspace class

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

import random

import pygame

from objects import AdvancedSpriteGroup, Airplane, Objective

class Airspace(pygame.rect.Rect):
    AIRSPACE_DIM = 100000
    MIN_OBJ_ALT = 7500
    MAX_ALTITUDE = 20000
    ALTITUDE_TOLERANCE = 1400
    ALTITUDE_WITHIN = 2000
    POINTS_REQUIRED = 10
    """The class for an airspace."""
    def __init__(self, x=(0, 0, 0, 0), y=None, w=None, h=None):
        """Initializes the instance."""
        if y == None: x, y, w, h = x # Input: 1 list
        elif w == None and h == None: (x, y), (w, h) = x, y # Input: 2 lists
        super(Airspace, self).__init__(x, y, self.AIRSPACE_DIM, self.AIRSPACE_DIM)
        self.planes = AdvancedSpriteGroup()
        self.objectives = AdvancedSpriteGroup()

    def __repr__(self):
        """Displays important informathion about the airspace."""
        return "%sx%s AIRSPACE\nPLANES:%s\nOBJECTIVES:%s" % (
                self.width, self.height,
                ''.join(["\n%s" % repr(plane) for plane in self.planes]),
                ''.join(["\n%s" % repr(obj) for obj in self.objectives]))
    
    def draw(self, screen, images):
        """Draws the airspace and everything inside it."""
        screen.blit(images['navcircle'], self.topleft)
        for plane in self.planes: 
            plane.draw(screen, images['navmarker'], self.x, self.y)
        for obj in self.objectives:
            obj.draw(screen, images['objectivemarker'], self.x, self.y)

    def update(self, *args, **kw):
        """Updates the airspace."""
        new_drawpos_multiplier = [
                self.AIRSPACE_DIM / self.width, 
                self.AIRSPACE_DIM / self.height
        ]
        self.planes.update(new_drawpos_multiplier)
        self.objectives.update(new_drawpos_multiplier)

        for plane in self.planes:
            collisions = pygame.sprite.spritecollide(plane,
                    self.objectives, True, self.collided)
            for collision in collisions:
                plane.points += 1
                self.generate_objective(collision.image)

    def add_plane(self, plane, player_id=None):
        """Adds a plane to the airspace.

        Creates a new airplane if an image is supplied.
        Returns the newly-added plane."""
        if type(plane) != Airplane:
            plane = Airplane(plane, self.AIRSPACE_DIM/2, self.AIRSPACE_DIM/2, 0, 
            drawpos_multiplier=[
                self.AIRSPACE_DIM / self.width, 
                self.AIRSPACE_DIM / self.height
            ], player_id=player_id)
        self.planes.add(plane)
        return plane

    def generate_objective(self, image):
        """Generates an objective."""
        objective = Objective(image, airspace_dim=self.size)
        # no collide, correct coords
        objective_correct = False
        while objective_correct != True:
            objective_correct = False
            # generate objective
            objective.draw_x = random.randint(0, self.width)
            objective.draw_z = random.randint(0, self.height)
            objective.altitude = random.randint(self.MIN_OBJ_ALT,
                    self.MAX_ALTITUDE)
            # test for collision
            if not pygame.sprite.spritecollide(objective, self.planes,
                    False, self.collided):
                objective_correct = True
        self.objectives.add(objective)

    def collided(self, airplane, objective,
            altitude_tolerance=None):
        """Tests if a airplane collides with an objective."""
        if altitude_tolerance == None:
            altitude_tolerance = Airspace.ALTITUDE_TOLERANCE
        return (airplane.rect.colliderect(objective.rect)
                and abs(objective.altitude - airplane.altitude)
                <= altitude_tolerance)

    def in_bounds(self, sprite, use_zeroed_coords=True):
        """Tests if an object is in bounds.

        If use_zeroed_coords is True, it will assume the airspace's
            topleft is (0, 0)."""
        if isinstance(sprite, pygame.sprite.Sprite):
            rect = sprite.rect
        else: rect = sprite
        if use_zeroed_coords:
            return (rect.left >= 0 and rect.top >= 0
                    and rect.right <= self.width
                    and rect.bottom <= self.height)
        else:
            return (rect.left >= self.left and rect.top >= self.top
                    and rect.right <= self.right
                    and rect.bottom <= self.bottom)
