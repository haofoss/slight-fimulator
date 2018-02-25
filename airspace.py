#!/usr/bin/env python

"""The Airspace class

Slight Fimulator - Flight simulator in Python
Copyright (C) 2017, 2018 Hao Tian and Adrien Hopkins

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
    """The class for an airspace."""
    AIRSPACE_DIM = 100000
    MIN_OBJ_ALT = 7500
    MAX_ALTITUDE = 20000
    ALTITUDE_TOLERANCE = 1400
    ALTITUDE_WITHIN = 2000
    POINTS_REQUIRED = 10
    def __init__(self, x=(0, 0, 0, 0), y=None, w=None, h=None):
        """Initialize the instance."""
        if y is None:
            x, y, w, h = x # Input: 1 list
        elif w is None and h is None:
            (x, y), (w, h) = x, y # Input: 2 lists
        super(Airspace, self).__init__(
            x, y, Airspace.AIRSPACE_DIM, Airspace.AIRSPACE_DIM)
        self.planes = AdvancedSpriteGroup()
        self.objectives = AdvancedSpriteGroup()

    def __repr__(self):
        """Display important informathion about the airspace."""
        return "{}x{} AIRSPACE\nPLANES:{}\nOBJECTIVES:{}".format(
            self.width, self.height,
            ''.join(["\n%s" % repr(plane) for plane in self.planes]),
            ''.join(["\n%s" % repr(obj) for obj in self.objectives]))

    def draw(self, client):
        """Draw the airspace and everything inside it."""
        client.screen.blit(
            client.images['navcircle'], client.airspace_rect)
        for plane in self.planes: # Draw planes
            plane.draw(client, self)
        for obj in self.objectives: # Draw objectives
            obj.draw(client, self)

    def update(self):
        """Update the airspace."""
        self.planes.update()

        for plane in self.planes: # Check for plane-objective collision
            collisions = pygame.sprite.spritecollide(
                plane, self.objectives, True, self.collided)
            for collision in collisions:
                plane.points += 1
                self.generate_objective()

    def add_plane(self, plane=None, player_id=None):
        """Add a plane to the airspace.

        Create a new airplane no plane is supplied.
        Created airplane is at the center of the airspace.
        Returns the newly-added plane."""
        if plane is None:
            plane = Airplane(
                self.width/2, self.height/2,
                self.width*0.06, self.height*0.06, 0,
                player_id=player_id)
        if isinstance(plane, Airplane):
            self.planes.add(plane)
            return plane
        raise TypeError("plane must be an Airplane or None.")

    def generate_objective(self):
        """Generate an objective."""
        objective = Objective(
            -1, -1, self.width*0.06, self.height*0.06, -1)
        # no collide; correct coords
        objective_correct = False
        while objective_correct != True:
            objective_correct = False
            # generate objective
            objective.x = random.randint(0, self.width)
            objective.z = random.randint(0, self.height)
            objective.altitude = random.randint(
                Airspace.MIN_OBJ_ALT, Airspace.MAX_ALTITUDE)
            # test for collision
            if not pygame.sprite.spritecollide(
                    objective, self.planes, False,
                    Airspace.collided):
                objective_correct = True
        self.objectives.add(objective)

    @staticmethod
    def collided(airplane, objective, altitude_tolerance=None):
        """Test if a airplane collides with an objective."""
        if altitude_tolerance is None:
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
