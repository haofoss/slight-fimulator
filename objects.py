#!/usr/bin/env python

"""The package's classes

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

import math
import os
import time

import pygame

PATH = os.path.dirname(os.path.realpath(__file__))


class Airplane(pygame.sprite.Sprite):
    """The class for an airplane sprite.

    All units are stored internally in SI base units
    """
    NEXT_ID = 0

    MAX_SPEED = 500
    TERMINAL_VELOCITY = MAX_SPEED / 5 # Why not?

    LABELS = "ID:\tX:\tY:\tALT:\tSPD:\tACCEL:\tVSPD:\t\
HDG:\tROLL:\tPITCH:\tPTS:\tDMG:\t"
    def __init__(self, x=(0, 0, 0, 0, 0), z=None, width=None,
                 height=None, altitude=None, player_id=None):
        """Initialize the instance."""
        super(Airplane, self).__init__()
        if z is None:
            x, z, width, height, altitude = x
        elif width is None:
            altitude = z
            x, z, width, height = x
        elif height is None:
            altitude = width
            width, height = z
            x, z = x
        if player_id is None: # Get an ID for the airplane
            self._id = Airplane.NEXT_ID
            Airplane.NEXT_ID += 1
        else: self._id = player_id
        # Initialize private variables
        self._pos = [x, z]
        self._size = [width, height]
        self._altitude = altitude
        self._heading = 0
        self._pitch = 0
        self._speed = 0
        self._acceleration = 0
        self._gravity = 0
        self._throttle = 0
        self._roll_level = 0
        self._vertical_roll_level = 0
        self._autopilot_info = {
            'enabled': False,
            'conditions': {
                'roll-centered': True,
                'vertical-roll-centered': True,
                'throttle-centered': True
            }
        }

        self._within_objective_range = False
        self._points = 0
        self._exit_code = 0
        self._health = 100
        self._time = time.time()

    def __repr__(self, show_labels=True):
        """Display some important stats about the plane."""
        msg = ("%i\t%i\t%i\t%i\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t\
%i\t%.1f\t" % (self.id_, self.x, self.z,
               self.altitude, self.speed, self.acceleration,
               self.vertical_velocity, self.heading, self.roll,
               self.pitch, self.points, 100 - self.health))
        if show_labels:
            return "%s\n%s" % (Airplane.LABELS, msg)
        else:
            return msg

    ## variables
    @property
    def id_(self):
        """Get the plane's ID."""
        return self._id
    @property
    def pos(self):
        """Get the plane's (x, z) position in metres."""
        return self._pos
    @pos.setter
    def pos(self, new_value):
        """Set the plane's (x, z) position in metres."""
        if not isinstance(new_value, (list, tuple)):
            raise TypeError("Position must be a list or a tuple.")
        if len(new_value) != 2:
            raise ValueError("Position must contain two values.")
        if not isinstance(new_value[0], (int, float)):
            raise ValueError("X must be a number.")
        if not isinstance(new_value[1], (int, float)):
            raise ValueError("Z must be a number.")
        self._pos = new_value
    @property
    def x(self):
        """Get the plane's x coordinate in metres."""
        return self._pos[0]
    @x.setter
    def x(self, new_value):
        """Set the plane's x coordinate in metres."""
        if not isinstance(new_value, (int, float)):
            raise ValueError("X must be a number")
        self._pos[0] = new_value
    @property
    def z(self):
        """Get the plane's z coordinate in metres."""
        return self._pos[1]
    @z.setter
    def z(self, new_value):
        """Set the plane's z coordinate in metres."""
        if not isinstance(new_value, (int, float)):
            raise ValueError("Z must be a number")
        self._pos[1] = new_value
    @property
    def altitude(self):
        """Get the plane's altitude in metres."""
        return self._altitude
    @altitude.setter
    def altitude(self, new_value):
        """Set the plane's altitude in metres."""
        if not isinstance(new_value, (int, float)):
            raise TypeError("Altitude must be a number.")
        self._altitude = new_value
    y = altitude
    @property
    def heading(self):
        """Get the plane's heading in radians."""
        return self._heading
    @heading.setter
    def heading(self, new_value):
        """Set the plane's heading in radians."""
        if not isinstance(new_value, (int, float)):
            raise TypeError("Heading must be a number.")
        new_value %= math.pi * 2
        self._heading = new_value
    @property
    def heading_degrees(self):
        """Get the plane's heading in degrees."""
        return math.degrees(self.heading)
    @heading_degrees.setter
    def heading_degrees(self, new_value):
        """Set the plane's heading in degrees."""
        self.heading = math.radians(new_value)
    @property
    def pitch(self):
        """Get the plane's pitch in radians."""
        return self._pitch
    @pitch.setter
    def pitch(self, new_value):
        """Set the plane's pitch in radians."""
        if not isinstance(new_value, (int, float)):
            raise TypeError("Pitch must be a number.")
        self._pitch = new_value
    @property
    def pitch_degrees(self):
        """Get the plane's pitch in degrees."""
        return math.degrees(self._pitch)
    @pitch_degrees.setter
    def pitch_degrees(self, new_value):
        """Set the plane's pitch in degrees."""
        self.pitch = math.radians(new_value)
    @property
    def speed(self):
        """Get the plane's speed in m/s."""
        return self._speed
    @speed.setter
    def speed(self, new_value):
        """Set the plane's speed in m/s."""
        if not isinstance(new_value, (int, float)):
            raise TypeError("Speed must be a number.")
        self._speed = new_value
    @property
    def horizontal_velocity(self):
        """Get the plane's horizontal speed in m/s."""
        return self.speed * math.cos(self.pitch)
    horizontal_speed = horizontal_velocity
    @property
    def vertical_velocity(self):
        """Get the plane's vertical speed in m/s."""
        return self.speed * math.sin(self.pitch)
    @property
    def gravity(self):
        """Get the plane's gravity-caused vertical speed drop in m/s."""
        return self._gravity
    @gravity.setter
    def gravity(self, new_value):
        """Set the plane's gravity-caused vertical speed drop in m/s."""
        if not isinstance(new_value, (int, float)):
            raise TypeError("Gravity must be a number.")
        self._gravity = new_value
    @property
    def total_vertical_velocity(self):
        """Get the plane's total vertical speed in m/s."""
        return self.vertical_velocity - self.gravity
    @property
    def acceleration(self):
        """Get the plane's acceleration in m/s."""
        return self._acceleration
    @acceleration.setter
    def acceleration(self, new_value):
        """Set the plane's acceleration in m/s."""
        if not isinstance(new_value, (int, float)):
            raise ValueError("Acceleration must be a number")
        self._acceleration = new_value
    @property
    def throttle(self):
        """Get the plane's throttle in m/s."""
        return self._throttle
    @throttle.setter
    def throttle(self, new_value):
        """Set the plane's throttle in m/s."""
        if not isinstance(new_value, (int, float)):
            raise ValueError("Throttle must be a number")
        if new_value < 0:
            new_value = 0
        elif new_value > 100:
            new_value = 100
        self._throttle = new_value
    @property
    def roll(self):
        """Get the plane's horizontal roll in radians."""
        return math.radians(self.roll_degrees)
    @property
    def roll_degrees(self):
        """Get the plane's horizontal roll in degrees."""
        return ((35/198) * self._roll_level**3 + (470/99)
                * self._roll_level)
    @property
    def roll_level(self):
        """Get the plane's horizontal roll level."""
        return self._roll_level
    @roll_level.setter
    def roll_level(self, new_value):
        """Set the plane's horizontal roll level."""
        if not isinstance(new_value, (int, float)):
            raise TypeError("Roll Level must be a number.")
        if new_value < -4:
            new_value = -4
        elif new_value > 4:
            new_value = 4
        self._roll_level = new_value
    @property
    def vertical_roll_level(self):
        """Get the plane's vertical roll level."""
        return self._vertical_roll_level
    @vertical_roll_level.setter
    def vertical_roll_level(self, new_value):
        """Set the plane's vertical roll level."""
        if not isinstance(new_value, (int, float)):
            raise TypeError("Vertical Roll Level must be a number.")
        if new_value < -4:
            new_value = -4
        elif new_value > 4:
            new_value = 4
        self._vertical_roll_level = new_value
    @property
    def autopilot_enabled(self):
        """Get the plane's autopilot's status."""
        if not self._autopilot_info['enabled']:
            return False
        else: # See if the autopilot can be disabled
            if abs(self.roll_level) < 0.1:
                self.roll_level = 0
                self._autopilot_info['conditions'][
                    'roll-centered'] = True
            if abs(self.vertical_roll_level) < 0.1:
                self.vertical_roll_level = 0
                self._autopilot_info['conditions'][
                    'vertical-roll-centered'] = True
            if abs(50 - self.throttle) < 1:
                self.throttle = 50
                self._autopilot_info['conditions'][
                    'throttle-centered'] = True
            if all(self._autopilot_info['conditions'].values()):
                self._autopilot_info['enabled'] = False
            return self._autopilot_info['enabled']
    @property
    def health(self):
        """Get the plane's health."""
        return self._health
    @health.setter
    def health(self, new_value):
        """Set the plane's health."""
        if not isinstance(new_value, (int, float)):
            raise TypeError("Health must be a number.")
        self._health = new_value
    @property
    def damage(self):
        """Get the plane's damage."""
        return 100-self._health
    @property
    def points(self):
        """Get the plane's score."""
        return self._points
    @points.setter
    def points(self, new_value):
        """Set the plane's score."""
        if not isinstance(new_value, (int, float)):
            raise TypeError("Score must be a number.")
        self._points = new_value
    score = points # score is an alias for points.
    @property
    def image(self):
        """Get the plane's image."""
        return self._image
    @property
    def rect(self):
        """Get the plane's rect."""
        return pygame.rect.Rect(self._pos, self._size)

    def enable_autopilot(self):
        """Enable the autopilot."""
        self._autopilot_info['enabled'] = True
        for condition in self._autopilot_info['conditions']:
            self._autopilot_info['conditions'][condition] = False

    def draw(self, client, airspace):
        """Draw the airplane."""
        image = pygame.transform.rotate(
            client.scaled_images['navmarker'], -self.heading_degrees)
        draw_rect = image.get_rect()
        draw_rect.center = (
            self.x / airspace.width * client.airspace_rect.width
            + client.airspace_rect.left,
            self.z / airspace.height * client.airspace_rect.height
            + client.airspace_rect.top
        )
        client.screen.blit(image, draw_rect)

    def update(self):
        """Update the plane."""
        tick_duration = time.time() - self._time
        self._time = time.time()

        # initialize damage
        damage = 0

        # stall and gravity
        if self.speed <= (self.MAX_SPEED / 5):
            max_vert_roll = max((self.speed-(self.MAX_SPEED / 10))
                                / (self.MAX_SPEED / 40), 0)
        else: max_vert_roll = 4
        self.gravity += (((self.MAX_SPEED / 10 - self.speed)
                          / self.MAX_SPEED * self.TERMINAL_VELOCITY)
                         - (self.gravity ** 2
                            / (self.TERMINAL_VELOCITY ** 2 / 10)))
        if self.gravity < 0:
            self.gravity = 0
        if self.altitude <= 0.1:
            self.gravity = 0

        # get heading and pitch
        self.heading += (self.roll * tick_duration)
        if self.vertical_roll_level > max_vert_roll:
            self.vertical_roll_level = max_vert_roll
        self.pitch_degrees = self.vertical_roll_level * 10

        # acceleration
        self.acceleration = (self.throttle**2 / 250
                             - self.speed**2 * 40 / self.MAX_SPEED**2)
        self.speed += (self.acceleration * tick_duration)

        # move plane
        hspeed = self.horizontal_speed * tick_duration
        vspeed = self.total_vertical_velocity * tick_duration
        self.x += math.sin(self.heading) * hspeed
        self.z -= math.cos(self.heading) * hspeed
        self.altitude += vspeed
        if self.altitude < 0.1:
            self.altitude = 0

        # overspeed damage
        if self.speed > self.MAX_SPEED * 0.75:
            damage += ((self.speed - self.MAX_SPEED*0.75) ** 2
                       / (self.MAX_SPEED**2*10) * tick_duration)
        if self._throttle > 75:
            damage += (self._throttle - 75) ** 2 / 1000 * tick_duration

        # autopilot
        if self.autopilot_enabled:
            self.roll_level *= (0.5 ** tick_duration)
            self.vertical_roll_level *= (0.5 ** tick_duration)
            self._throttle = 50 + (self.throttle-50) * (
                0.5 ** tick_duration)

        # deal damage
        self.health -= damage

    # Function that approximates the 5, 10, 20, 30
    # roll of Slight Fimulator 1.0
    get_roll = lambda s, r: (35/198) * r**3 + (470/99) * r
    get_pitch = lambda s, r: 10*r


class Objective(pygame.sprite.Sprite):
    """The class for an objective sprite."""
    NEXT_ID = 0

    LABELS = "ID:\tX:\tY:\tALT:\t"
    def __init__(self, x=(0, 0, 0, 0, 0), z=None, width=None,
                 height=None, altitude=None, obj_id=None):
        """Initialize the instance."""
        super(Objective, self).__init__()
        if z is None:
            x, z, width, height, altitude = x
        elif width is None:
            altitude = z
            x, z, width, height = x
        elif height is None:
            altitude = width
            width, height = z
            x, z = x
        if obj_id is None: # Get an ID for the objective
            self._id = Objective.NEXT_ID
            Objective.NEXT_ID += 1
        else: self._id = obj_id
        # Initialize private variables
        self._pos = [x, z]
        self._size = [width, height]
        self._altitude = altitude

    def __repr__(self, show_labels=True):
        """Display some important stats about the objective."""
        msg = "%i\t%i\t%i\t%i\t" % (self.id_, self.x, self.z,
                                    self.altitude)
        if show_labels:
            return "%s\n%s" % (self.labels(), msg)
        else:
            return msg

    @property
    def id_(self):
        """Get the objective's ID."""
        return self._id
    @property
    def pos(self):
        """Get the objective's (x, z) position in metres."""
        return self._pos
    @pos.setter
    def pos(self, new_value):
        """Set the objective's (x, z) position in metres."""
        if not isinstance(new_value, (list, tuple)):
            raise TypeError("Position must be a list or a tuple.")
        if len(new_value) != 2:
            raise ValueError("Position must contain two values.")
        if not isinstance(new_value[0], (int, float)):
            raise ValueError("X must be a number.")
        if not isinstance(new_value[1], (int, float)):
            raise ValueError("Z must be a number.")
        self._pos = new_value
    @property
    def x(self):
        """Get the objective's x coordinate in metres."""
        return self._pos[0]
    @x.setter
    def x(self, new_value):
        """Set the objective's x coordinate in metres."""
        if not isinstance(new_value, (int, float)):
            raise ValueError("X must be a number")
        self._pos[0] = new_value
    @property
    def z(self):
        """Get the objective's z coordinate in metres."""
        return self._pos[1]
    @z.setter
    def z(self, new_value):
        """Set the objective's z coordinate in metres."""
        if not isinstance(new_value, (int, float)):
            raise ValueError("Z must be a number")
        self._pos[1] = new_value
    @property
    def altitude(self):
        """Get the objective's altitude in metres."""
        return self._altitude
    @altitude.setter
    def altitude(self, new_value):
        """Set the objective's altitude in metres."""
        if not isinstance(new_value, (int, float)):
            raise TypeError("Altitude must be a number.")
        self._altitude = new_value
    y = altitude
    @property
    def image(self):
        """Get the objective's image."""
        return self._image
    @property
    def rect(self):
        """Get the plane's rect."""
        return pygame.rect.Rect(self._pos, self._size)

    def draw(self, client, airspace):
        """Draw the objective."""
        draw_rect = client.scaled_images['objectivemarker'].get_rect()
        draw_rect.center = (
            self.x / airspace.width * client.airspace_rect.width
            + client.airspace_rect.left,
            self.z / airspace.height * client.airspace_rect.height
            + client.airspace_rect.top
        )
        client.screen.blit(
            client.scaled_images['objectivemarker'], draw_rect)


class AdvancedSpriteGroup(pygame.sprite.Group):
    """A Pygame sprite group, except you can index it."""
    def __init__(self, *args, **kw):
        """Initialize the instance."""
        super(AdvancedSpriteGroup, self).__init__(*args, **kw)

    def __getitem__(self, key):
        """Get the sprite at key."""
        for sprite in self:
            if sprite.id_ == key:
                return sprite
            raise KeyError("Item {} not found.".format(key))
