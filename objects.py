#!/usr/bin/env python3

"""The package's classes

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
    def __init__(self, image, x=(0, 0, 0), y=None, altitude=None,
            player_id=None, drawpos_multiplier=None):
        """Initializes the instance."""
        super(Airplane, self).__init__()
        if y == None and altitude != None: x, y = x
        elif y == None: x, y, altitude = x
        
        if player_id == None: self._id = Airplane.NEXT_ID; Airplane.NEXT_ID += 1
        else: self._id = player_id
        
        self._drawpos_multiplier = drawpos_multiplier
        self._pos = [x, y]
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

        self._image = image

    def __repr__(self, show_labels=True):
        """Displays some important stats about the plane."""
        msg = ("%i\t%i\t%i\t%i\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t\
%i\t%.1f\t" % (self.id_, self.x, self.z,
                self.altitude, self.speed, self.acceleration,
                self.vertical_velocity, self.heading, self.roll, self.pitch,
                self.points, 100 - self.health))
        if show_labels: return "%s\n%s" % (self.labels(), msg)
        else: return msg

    ## variables
    @property
    def id_(self):
        return self._id
    @property
    def pos(self):
        return self._pos
    @pos.setter
    def pos(self, new_value):
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
        return self._pos[0]
    @x.setter
    def x(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise ValueError("X must be a number")
        self._pos[0] = new_value
    @property
    def z(self):
        return self._pos[1]
    @z.setter
    def z(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise ValueError("Z must be a number")
        self._pos[1] = new_value
    @property
    def draw_pos(self):
        return [self.x / self._drawpos_multiplier[0],
                self.z / self._drawpos_multiplier[1]]
    @draw_pos.setter
    def draw_pos(self, new_value):
        if not isinstance(new_value, (list, tuple)):
            raise TypeError("Position must be a list or a tuple.")
        if len(new_value) != 2:
            raise ValueError("Position must contain two values.")
        if not isinstance(new_value[0], (int, float)):
            raise ValueError("X must be a number.")
        if not isinstance(new_value[1], (int, float)):
            raise ValueError("Z must be a number.")
        self._pos[0] = self.rect.centerx * self._drawpos_multiplier[0]
        self._pos[1] = self.rect.centery * self._drawpos_multiplier[1]
    @property
    def draw_x(self):
        return self.x / self._drawpos_multiplier[0]
    @draw_x.setter
    def draw_x(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise ValueError("Z must be a number")
        self._pos[0] = new_value * self._drawpos_multiplier[0]
    @property
    def draw_z(self):
        return self.z / self._drawpos_multiplier[1]
    @draw_z.setter
    def draw_z(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise ValueError("Z must be a number")
        self._pos[1] = new_value * self._drawpos_multiplier[1]
    @property
    def altitude(self):
        return self._altitude
    @altitude.setter
    def altitude(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise TypeError("Altitude must be a number.")
        self._altitude = new_value
    y = altitude
    @property
    def heading(self):
        return self._heading
    @heading.setter
    def heading(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise TypeError("Heading must be a number.")
        new_value %= math.pi * 2
        self._heading = new_value
    @property
    def heading_degrees(self):
        return math.degrees(self.heading)
    @heading_degrees.setter
    def heading_degrees(self, new_value):
        self.heading = math.radians(new_value)
    @property
    def pitch(self):
        return self._pitch
    @pitch.setter
    def pitch(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise TypeError("Pitch must be a number.")
        self._pitch = new_value
    @property
    def pitch_degrees(self):
        return math.degrees(self._pitch)
    @pitch_degrees.setter
    def pitch_degrees(self, new_value):
        self.pitch = math.radians(new_value)
    @property
    def speed(self):
        return self._speed
    @speed.setter
    def speed(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise TypeError("Velocity must be a number.")
        self._speed = new_value
    @property
    def horizontal_velocity(self):
        return self.speed * math.cos(self.pitch)
    horizontal_speed = horizontal_velocity
    @property
    def vertical_velocity(self):
        return self.speed * math.sin(self.pitch)
    @property
    def gravity(self):
        return self._gravity
    @gravity.setter
    def gravity(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise TypeError("Gravity must be a number.")
        self._gravity = new_value
    @property
    def total_vertical_velocity(self):
        return self.vertical_velocity - self.gravity
    @property
    def acceleration(self):
        return self._acceleration
    @acceleration.setter
    def acceleration(self, new_value):
        if not isinstance(new_value, (int,  float)):
            raise ValueError("Acceleration must be a number")
        self._acceleration = new_value
    @property
    def throttle(self):
        return self._throttle
    @throttle.setter
    def throttle(self, new_value):
        if not isinstance(new_value, (int,  float)):
            raise ValueError("Throttle must be a number")
        if not (0 <= new_value <= 100):
            raise ValueError("Throttle must be 0-100")
        self._throttle = new_value
    @property
    def roll(self):
        return math.radians(self.roll_degrees)
    @property
    def roll_degrees(self):
        return (35/198) * self._roll_level**3 + (470/99) * self._roll_level
    @property
    def roll_level(self):
        return self._roll_level
    @roll_level.setter
    def roll_level(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise TypeError("Roll Level must be a number.")
        self._roll_level = new_value
    @property
    def vertical_roll_level(self):
        return self._vertical_roll_level
    @vertical_roll_level.setter
    def vertical_roll_level(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise TypeError("Vertical Roll Level must be a number.")
        self._vertical_roll_level = new_value
    @property
    def autopilot_enabled(self):
        if not self._autopilot_info['enabled']: return False
        else: # See if the autopilot can be disabled
            if abs(self.roll_level) < 0.1:
                self.roll_level = 0
                self._autopilot_info['conditions']['roll-centered'] = True
            if abs(self.vertical_roll_level) < 0.1:
                self.vertical_roll_level = 0
                self._autopilot_info['conditions'][
                        'vertical-roll-centered'] = True
            if abs(50 - self._throttle) < 1:
                self._throttle = 50
                self._autopilot_info['conditions']['throttle-centered'] = True
            if all(self._autopilot_info['conditions'].values()):
                self._autopilot_info['enabled'] = False
            return self._autopilot_info['enabled']
    @property
    def health(self):
        return self._health
    @health.setter
    def health(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise TypeError("Health must be a number.")
        self._health = new_value
    @property
    def damage(self):
        return 100-self._health
    @property
    def points(self):
        return self._points
    @points.setter
    def points(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise TypeError("Score must be a number.")
        self._points = new_value
    score = points # score is an alias for points.
    @property
    def image(self):
        return self._image
    @property
    def rect(self):
        rect_ = self.image.get_rect()
        rect_.center = [self.x / self._drawpos_multiplier[0],
                self.z / self._drawpos_multiplier[1]]
        return rect_
        
    def enable_autopilot(self):
        self._autopilot_info['enabled'] = True
        for condition in self._autopilot_info['conditions']:
            self._autopilot_info['conditions'][condition] = False
    
    def labels(self):
        """Outputs the labels used in __repr__."""
        return ("ID:\tX:\tY:\tALT:\tSPD:\tACCEL:\tVSPD:\t\
HDG:\tROLL:\tPITCH:\tPTS:\tDMG:\t")

    def draw(self, screen, airspace_x, airspace_y=None):
        """Draws the airplane."""
        if airspace_y == None: airspace_x, airspace_y = airspace_x
        image_rotated = pygame.transform.rotate(self._image,
            -self.heading_degrees)
        draw_rect = image_rotated.get_rect()
        draw_rect.center = self.rect.center
        draw_rect.x += airspace_x
        draw_rect.y += airspace_y
        screen.blit(image_rotated, draw_rect)

    def update(self):
        """Updates the plane."""
        tick_duration = time.time() - self._time
        self._time = time.time()
        
        # initialize damage
        damage = 0

        # stall and gravity
        if self.speed <= 100:
            max_vert_roll = max((self.speed-50) / 12.5, 0)
        else: max_vert_roll = 4
        self.gravity += (((50 - self.speed) / 50 * 10)
             - (self.gravity ** 2 / 1000))
        if self.gravity < 0: self.gravity = 0
        if self.altitude <= 0.1: self.gravity = 0
        
        # move the plane
        self.heading += (self.roll * tick_duration)
        if self.vertical_roll_level > max_vert_roll:
            self.vertical_roll_level = max_vert_roll
        self.pitch_degrees = self.get_pitch(self.vertical_roll_level)

        # acceleration
        self.acceleration = (self.throttle ** 2 / 250
                - self.speed ** 2 / 6250)
        self.speed += (self.acceleration * tick_duration)
        
        hspeed = self.horizontal_speed * tick_duration
        vspeed = self.total_vertical_velocity * tick_duration
        self.x += math.sin(self.heading) * hspeed
        self.z -= math.cos(self.heading) * hspeed
        self.altitude += vspeed
        if self.altitude < 0.1: self.altitude = 0

        # overspeed damage
        if self.speed > 375:
            damage += (self.speed - 375) ** 2 / 25000 * tick_duration
        if self._throttle > 75:
            damage += (self._throttle - 75) ** 2 / 1000 * tick_duration

        # autopilot
        if self.autopilot_enabled:
            self.roll_level *= (0.5 ** tick_duration)
            self.vertical_roll_level *= (0.5 ** tick_duration)
            self._throttle = 50 + (self.throttle-50) * (0.5 ** tick_duration)
##            window.status = ["Autopilot engaged..."]
##            if not self.autopilot_enabled:
##                window.sounds['apdisconnect'].play()

        # deal damage
        self.health -= damage

    # Function that approximates the 5, 10, 20, 30 roll of Slight Fimulator 1.0
    get_roll = lambda s, r: (35/198) * r**3 + (470/99) * r
    get_pitch = lambda s, r: 10*r


class Objective(pygame.sprite.Sprite):
    """The class for an objective sprite."""
    NEXT_ID = 0
    def __init__(self, image, x=(0, 0, 0), y=None, altitude=None, obj_id=None,
            airspace_dim=[700, 700]):
        """Initializes the instance."""
        super(Objective, self).__init__()
        if y == None and altitude != None: x, y = x
        elif y == None: x, y, altitude = x
        
        if obj_id == None: self._id = Objective.NEXT_ID; Objective.NEXT_ID += 1
        else: self._id = obj_id
        self._drawpos_multiplier = [100000 / i for i in airspace_dim]
        self._pos = [x, y]
        self._altitude = altitude
        self._image = image

    def __repr__(self, show_labels=True):
        msg = "%i\t%i\t%i\t%i\t" % (self.id_, self.x, self.z,
                self.altitude)
        if show_labels: return "%s\n%s" % (self.labels(), msg)
        else: return msg
    
    @property
    def id_(self):
        return self._id
    @property
    def pos(self):
        return self._pos
    @pos.setter
    def pos(self, new_value):
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
        return self._pos[0]
    @x.setter
    def x(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise ValueError("X must be a number")
        self._pos[0] = new_value
    @property
    def z(self):
        return self._pos[1]
    @z.setter
    def z(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise ValueError("Z must be a number")
        self._pos[1] = new_value
    @property
    def draw_pos(self):
        return [self.x / self._drawpos_multiplier[0],
                self.z / self._drawpos_multiplier[1]]
    @draw_pos.setter
    def draw_pos(self, new_value):
        if not isinstance(new_value, (list, tuple)):
            raise TypeError("Position must be a list or a tuple.")
        if len(new_value) != 2:
            raise ValueError("Position must contain two values.")
        if not isinstance(new_value[0], (int, float)):
            raise ValueError("X must be a number.")
        if not isinstance(new_value[1], (int, float)):
            raise ValueError("Z must be a number.")
        self._pos[0] = self.rect.centerx * self._drawpos_multiplier[0]
        self._pos[1] = self.rect.centery * self._drawpos_multiplier[1]
    @property
    def draw_x(self):
        return self.x / self._drawpos_multiplier[0]
    @draw_x.setter
    def draw_x(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise ValueError("Z must be a number")
        self._pos[0] = new_value * self._drawpos_multiplier[0]
    @property
    def draw_z(self):
        return self.z / self._drawpos_multiplier[1]
    @draw_z.setter
    def draw_z(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise ValueError("Z must be a number")
        self._pos[1] = new_value * self._drawpos_multiplier[1]
    @property
    def altitude(self):
        return self._altitude
    @altitude.setter
    def altitude(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise TypeError("Altitude must be a number.")
        self._altitude = new_value
    y = altitude
    @property
    def image(self):
        return self._image
    @property
    def rect(self):
        rect_ = self.image.get_rect()
        rect_.center = [self.x / self._drawpos_multiplier[0],
                self.z / self._drawpos_multiplier[1]]
        return rect_

    def labels(self):
        """Outputs the labels used in __repr__."""
        return "ID:\tX:\tY:\tALT:\t"

    def draw(self, screen, airspace_x, airspace_y=None):
        """Draws the objective."""
        if airspace_y == None: airspace_x, airspace_y = airspace_x
        draw_rect = self.rect.copy()
        draw_rect.x += airspace_x
        draw_rect.y += airspace_y
        screen.blit(self.image, draw_rect)


class AdvancedSpriteGroup(pygame.sprite.Group):
    """A Pygame sprite group, except you can index it."""
    def __init__(self, *args, **kw):
        super(AdvancedSpriteGroup, self).__init__()

    def __getitem__(self, key):
        for sprite in self:
            if sprite.id_ == key:
                return sprite
            raise Exception("Item {} not found.".format(key))
