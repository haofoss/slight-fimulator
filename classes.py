#!/usr/bin/env python
# -*- coding:utf-8 -*-

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

import datetime
import math
import os
import random
import time

import pygame

try:
    import unofficial_utilities_for_pygame as utils
    from __init__ import __author__, __version__
    from constants import *
    from functions import *
except:
    from . import unofficial_utilities_for_pygame as utils
    from .__init__ import __author__, __version__
    from .constants import *
    from .functions import *

PATH = os.path.dirname(os.path.realpath(__file__))


class Airplane(utils.ImprovedSprite):
    """The class for an airplane sprite.
    
    All units are stored internally in SI base units."""
    NEXT_ID = 0
    def __init__(self, image, x=(0, 0, 0), y=None, altitude=None,
            speed=0, throttle=0, player_id=None, airspace_dim=[700, 700]):
        """Initializes the instance."""
        if y == None and altitude != None: x, y = x
        elif y == None: x, y, altitude = x
        super(Airplane, self).__init__(image, x, y)
        self._pos = list(self.rect.center)
        self._upos_multiplier = [100000 / i for i in airspace_dim]
        self._altitude = altitude
        self._heading = 0
        self._pitch = 0
        self._speed = speed
        self._acceleration = 0
        self.gravity = 0
        self.gravity_force = 0
        self.max_vert_roll = 0
        self._throttle = throttle
        self._roll_level = 0
        self._vertical_roll_level = 0
        self.ap_cond = [1, 1, 1]
        self.ap_enabled = False

        self.within_objective_range = False
        self._points = 0
        self.exit_code = 0
        self._health = 100
        self.warnings = []
        if player_id == None: self.id = Airplane.NEXT_ID; Airplane.NEXT_ID += 1
        else: self.id = player_id

    def __repr__(self, show_labels=True):
        """Displays some important stats about the plane."""
        msg = ("%i\t%.1f\t%.1f\t%i\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t\
%i\t%.1f\t" % (self.id, self.upos[0] / 1000, self.upos[1] / 1000,
                self.altitude, self.speed, self.acceleration,
                self.vertical_velocity, self.heading, self.roll, self.pitch,
                self.points, 100 - self.health))
        if show_labels: return "%s\n%s" % (self.labels(), msg)
        else: return msg

    ## variables
    @property
    def pos(self):
        return self._pos
    @pos.setter
    def pos(self, new_value):
        if not isinstance(new_value, (list, tuple)):
            raise TypeError("Position must be a list or a tuple.")
        if len(new_value) != 2:
            raise ValueError("Position must contain two values.")
        self.x, self.z = new_value
        self.rect.center = self._pos
    @property
    def x(self):
        return self._pos[0]
    @x.setter
    def x(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise ValueError("X must be a number")
        self._pos[0] = new_value
        self.rect.centerx = self._pos[0]
    @property
    def z(self):
        return self._pos[1]
    @z.setter
    def z(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise ValueError("Z must be a number")
        self._pos[1] = new_value
        self.rect.centery = self._pos[1]
    @property
    def upos(self):
        return [self.x * self._upos_multiplier[0],
                self.z * self._upos_multiplier[1]]
    @property
    def ux(self):
        return self.x * self._upos_multiplier[0]
    @property
    def uz(self):
        return self.z * self._upos_multiplier[1]
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
    def acceleration(self):
        return self._acceleration
    @acceleration.setter
    def acceleration(self, new_value):
        if not isinstance(new_value, (int,  float)):
            raise ValueError("Acceleration must be a number")
        self._acceleration = new_value
    @property
    def roll(self):
        return math.radians((35/198) * self._roll_level**3 + (470/99) * self._roll_level)
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
    
    def labels(self):
        """Outputs the labels used in __repr__."""
        return ("ID:\tX:\tY:\tALT:\tSPD:\tACCEL:\tVSPD:\t\
HDG:\tROLL:\tPITCH:\tPTS:\tDMG:\t")

    def draw(self, screen, airspace_x, airspace_y=None):
        """Draws the airplane."""
        if airspace_y == None: airspace_x, airspace_y = airspace_x
        image_rotated = pygame.transform.rotate(self.image, -self.heading_degrees)
        draw_rect = self.rect.copy()
        draw_rect.x += airspace_x
        draw_rect.y += airspace_y
        screen.blit(image_rotated, draw_rect)

    def update(self, window=None):
        """Updates the plane."""
        if window.fps == 0: window.fps = window.max_fps
        # calculate display stretch
        x_str = window.airspace.width / AIRSPACE_DIM
        y_str = window.airspace.height / AIRSPACE_DIM

        # initialize damage
        damage = 0
        
        # move the plane
        self.heading += (self.roll / window.fps)
        if self.vertical_roll_level > self.max_vert_roll:
            self.vertical_roll_level = self.max_vert_roll
        self.pitch_degrees = self.get_pitch(self.vertical_roll_level)

        # acceleration
        self.acceleration = (self._throttle ** 2 / 250
                - self.speed ** 2 / 6250)
        self.speed += (self.acceleration / window.fps)

        # stall and gravity
        if self.speed <= 100:
            if self.altitude != 0:
                window.warnings['stall'] = True
            self.max_vert_roll = max((self.speed-50) / 12.5, 0)
        else: self.max_vert_roll = 4
        self.gravity_force += (((50 - self.speed) / 50 * 10)
             - (self.gravity_force ** 2 / 1000))
        if self.gravity_force < 0: self.gravity_force = 0
        if self.altitude <= 0.1: self.gravity = 0
        else: self.gravity = self.gravity_force
        self.total_vertical_velocity = self.vertical_velocity - self.gravity
        if self.total_vertical_velocity < -self.altitude:
            self.total_vertical_velocity = -self.altitude
        
        hspeed = self.horizontal_speed / window.fps
        vspeed = self.total_vertical_velocity / window.fps
        self.x += math.sin(self.heading) * hspeed * x_str
        self.z -= math.cos(self.heading) * hspeed * y_str
        self.rect.center = tuple(self.pos)
        self.altitude += vspeed
        if self.altitude < 0.1: self.altitude = 0

        # overspeed damage
        if self.speed > 375:
            window.warnings['overspeed'] = True
            damage += (self.speed - 375) ** 2 / 25000 / window.fps
        if self._throttle > 75:
            damage += (self._throttle - 75) ** 2 / 1000 / window.fps

        # height warnings
        if self.altitude <= 500 and not window.ignore_warnings \
                and self.total_vertical_velocity <= -20:
            window.warnings['pulluploop'] = True
            window.status = ["PRESS AND HOLD", "THE \"DOWN\" KEY!"]
        elif (self.altitude < 1000 and self.total_vertical_velocity > 0
                and self._throttle < 50) and not window.ignore_warnings:
            window.warnings['dontsinkloop'] = True
            window.status = ["Be careful not to stall."]
        elif (self.altitude < 1000 and self.speed > 250
                and not window.ignore_warnings):
            window.warnings["terrainloop"] = True
        elif (self.altitude < 1000 and self.speed <= 250
                and self.total_vertical_velocity <= -20
                and not window.ignore_warnings):
            window.warnings['pulluploop2'] = True
            window.status = ["DO NOT DESCEND!"]
        elif (abs(self.altitude - window.closest_objective.altitude)
                <= ALTITUDE_WITHIN):
            window.status = ["Approaching objective", "altitude..."]
            # if we just entered objective altitude range
            if not self.within_objective_range:
                window.warnings["altitude"] = True
                self.within_objective_range = True
        # if we are outside objective altitude range
        elif not window.ignore_warnings:
            self.within_objective_range = False
            window.status = ["Fly to the objective."]
        elif window.ignore_warnings == 1:
            window.status = ["Fly up above 1000 m!"]
            if self.altitude > 1000:
                window.ignore_warnings = 0
        if abs(self.roll) >= 30:
            window.warnings['bankangle'] = True

        # disable loops
        if self.altitude > 500:
            window.warnings['pulluploop'] = False
        if not (self.altitude < 1000 and self.vertical_velocity > 0
                and self._throttle < 50):
            window.warnings['dontsinkloop'] = False
        if not (self.altitude < 1000 and self.speed > 250):
            window.warnings["terrainloop"] = False
        if not (self.altitude < 1000 and self.speed <= 250):
            window.warnings['pulluploop2'] = False

        # autopilot
        if self.ap_enabled:
            self.roll_level *= (0.5 ** (1/window.fps))
            self.vertical_roll_level *= (0.5 ** (1/window.fps))
            self._throttle = 50 + (self._throttle-50) * (0.5 ** (1/window.fps))
            window.status = ["Autopilot engaged..."]
            if abs(self.roll_level) < 0.1:
                self.roll_level = 0
                self.ap_cond[0] = True
            else: self.ap_cond[0] = False
            if abs(self.vertical_roll_level) < 0.1:
                self.vertical_roll_level = 0
                self.ap_cond[1] = True
            else: self.ap_cond[0] = False
            if abs(50 - self._throttle) < 1:
                self._throttle = 50
                self.ap_cond[2] = True
            else: self.ap_cond[0] = False
            if self.ap_cond[0] and self.ap_cond[1] and self.ap_cond[2]:
                self.ap_enabled = False
                window.sounds['apdisconnect'].play()

        # check for almost-collision
        if (pygame.sprite.spritecollide(self, pygame.sprite.GroupSingle(
                window.closest_objective), False) and abs(self.altitude
                - window.closest_objective.altitude) > ALTITUDE_TOLERANCE):
            window.status = ["Objective NOT complete.", "Check OBJ ALT"]

        # deal damage
        self.health -= damage
        if self.health <= 0:
            self.exit_code = 5
        elif self.points >= POINTS_REQUIRED and self.altitude <= 0:
            self.exit_code = 1
        elif self.points >= POINTS_REQUIRED:
            window.status = ["All objectives found!",
                    "Return to ground level."]
            window.ignore_warnings = 2

        # position-related exit
        if self.altitude > MAX_ALTITUDE:
            self.exit_code = 6
        elif self.altitude <= 0 and self.total_vertical_velocity < -20:
            self.exit_code = 3
        elif self.altitude <= 0 and self.total_vertical_velocity >= -20:
            self.altitude = 0
        elif not window.airspace.in_bounds(self):
            self.exit_code = 4

    # Function that approximates the 5, 10, 20, 30 roll of Slight Fimulator 1.0
    get_roll = lambda s, r: (35/198) * r**3 + (470/99) * r
    get_pitch = lambda s, r: 10*r


class Objective(utils.ImprovedSprite):
    """The class for an objective sprite."""
    NEXT_ID = 0
    def __init__(self, image, x=(0, 0, 0), y=None, altitude=None, obj_id=None,
            airspace_dim=[700, 700]):
        """Initializes the instance."""
        if y == None and altitude != None: x, y = x
        elif y == None: x, y, altitude = x
        super(Objective, self).__init__(image, x, y)
        self._pos = list(self.rect.center)
        self._upos_multiplier = [100000 / i for i in airspace_dim]
        self._altitude = altitude

        if obj_id == None: self.id = Objective.NEXT_ID; Objective.NEXT_ID += 1
        else: self.id = obj_id

    def __repr__(self, show_labels=True):
        msg = "%i\t%.1f\t%.1f\t%i\t" % (self.id, self.upos[0] / 1000,
                self.upos[1] / 1000, self.altitude)
        if show_labels: return "%s\n%s" % (self.labels(), msg)
        else: return msg
        
    @property
    def pos(self):
        return self._pos
    @pos.setter
    def pos(self, new_value):
        if not isinstance(new_value, (list, tuple)):
            raise TypeError("Position must be a list or a tuple.")
        if len(new_value) != 2:
            raise ValueError("Position must contain two values.")
        self.x, self.z = new_value
        self.rect.center = self._pos
    @property
    def x(self):
        return self._pos[0]
    @x.setter
    def x(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise ValueError("X must be a number")
        self._pos[0] = new_value
        self.rect.centerx = self._pos[0]
    @property
    def z(self):
        return self._pos[1]
    @z.setter
    def z(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise ValueError("Z must be a number")
        self._pos[1] = new_value
        self.rect.centery = self._pos[1]
    @property
    def upos(self):
        return [self.x * self._upos_multiplier[0],
                self.z * self._upos_multiplier[1]]
    @property
    def ux(self):
        return self.x * self._upos_multiplier[0]
    @property
    def uz(self):
        return self.z * self._upos_multiplier[1]
    @property
    def altitude(self):
        return self._altitude
    @altitude.setter
    def altitude(self, new_value):
        if not isinstance(new_value, (int, float)):
            raise TypeError("Altitude must be a number.")
        self._altitude = new_value
    y = altitude

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


class Airspace(pygame.rect.Rect):
    """The class for an airspace."""
    def __init__(self, x=(0, 0, 0, 0), y=None, w=None, h=None):
        """Initializes the instance."""
        if y == None: x, y, w, h = x # Input: 1 list
        elif w == None and h == None: (x, y), (w, h) = x, y # Input: 2 lists
        super(Airspace, self).__init__(x, y, w, h)
        self.panel = pygame.rect.Rect(x-(w/140), y-(h/140), w*71/70, h*71/70)
        self.planes = pygame.sprite.Group()
        self.objectives = pygame.sprite.Group()

    def __repr__(self):
        """Displays important informathion about the airspace."""
        return "%sx%s AIRSPACE\nPLANES:%s\nOBJECTIVES:%s" % (
                self.width, self.height,
                ''.join(["\n%s" % repr(plane) for plane in self.planes]),
                ''.join(["\n%s" % repr(obj) for obj in self.objectives]))

    def draw(self, screen, image, color, panel_color):
        """Draws the airspace and everything inside it."""
        pygame.draw.rect(screen, panel_color, self.panel)
        pygame.draw.rect(screen, color, self)
        screen.blit(image, (self.topleft))
        for plane in self.planes: plane.draw(screen, self.x, self.y)
        for obj in self.objectives: obj.draw(screen, self.x, self.y)

    def update(self, window, *args, **kw):
        """Updates the airspace."""
        self.planes.update(window, *args)
        self.objectives.update(window, *args)

        for plane in self.planes:
            collisions = pygame.sprite.spritecollide(plane,
                    self.objectives, True, self.collided)
            for collision in collisions:
                plane.points += 1
                self.generate_objective(collision.image)
                window.status = ["Fly to the objective."]

    def add_plane(self, plane, player_id=None):
        """Adds a plane to the airspace.

        Creates a new airplane if an image is supplied.
        Returns the newly-added plane."""
        if type(plane) != Airplane:
            plane = Airplane(plane, self.width/2, self.height/2,
                    0, airspace_dim=self.size, player_id=player_id)
        self.planes.add(plane)
        return plane

    def generate_objective(self, image):
        """Generates an objective."""
        objective = Objective(image, airspace_dim=self.size)
        # no collide, correct coords
        objective_correct = [False, False]
        while objective_correct != [True, True]:
            objective_correct = [False, False]
            # generate objective
            objective.x = random.randint(0, self.width)
            objective.z = random.randint(0, self.height)
            objective.altitude = random.randint(MIN_OBJ_ALT, MAX_ALTITUDE)
            # test for collision
            if not pygame.sprite.spritecollide(objective, self.planes,
                    False, self.collided):
                objective_correct[0] = True
            if self.in_bounds(objective):
                objective_correct[1] = True
        self.objectives.add(objective)

    def collided(self, airplane, objective,
            altitude_tolerance=ALTITUDE_TOLERANCE):
        """Tests if a airplane collides with an objective."""
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


class Game(utils.Game):
    """The main window for the game."""
    GAME_STAGES = {}
    GAME_LOOPS = {}
    DEFAULT_SIZE = (1280, 960)
    NEXT_ID = 0
    EXIT_TITLES = [
            "UNEXPECTED",
            "Congratulations",
            "Closed",
            "Failed",
            "Failed",
            "Failed",
            "Failed",
            "UNEXPECTED"
    ]
    EXIT_REASONS = [
            "Exited with exitcode 0 (unexpected). Please report.",
            "You have completed the objective with a score of %i.",
            "The game has been closed. Your score was %i.",
            "You crashed your aircraft. Your score was %i.",
            "Left the operation area. Your score was %i.",
            "The aircraft was overstressed. Your score was %i.",
            "The aircraft exceeded its service ceiling altitude.  \
Your score was %i.",
            "Exited with exitcode 7 (unexpected). Please report."
    ]
    def __init__(self, size=DEFAULT_SIZE, player_id=None):
        """Initializes the instance. Does not start the game."""
        # Finds a folder if possible, otherwise tries a zip archive
        if "resources" in os.listdir(PATH):
            resources_path = "%s/resources" % PATH
        elif "resources.zip" in os.listdir(PATH):
            resources_path = "%s/resources.zip" % PATH
        else: raise Exception("No resources found!")
        super(Game, self).__init__(
                resources_path=resources_path,
                title="Slight Fimulator v%s" % __version__,
                icontitle="Slight Fimulator",
                size=size, bg=utils.Game.BG_PRESETS['bg-color'])
        self.max_fps = 60
        self.prev_size = self.size
        self.unit_id = 0
        if player_id == None: self.id = Game.NEXT_ID; Game.NEXT_ID += 1
        else: self.id = player_id
        self.key_held = [0, 0, 0]

    def __repr__(self):
        """Prints important information about the game."""
        return ("===== GAME ID %i =====\nAIRSPACE: %s\n===== GAME ID %i ====="
                % (self.id, repr(self.airspace), self.id))

    # -------------------------------------------------------------------------
    # STARTUP CODE
    # -------------------------------------------------------------------------

    def startup(self):
        """A function that is run once on startup."""
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()

        self.images['logo'] = pygame.transform.scale(self.images['logo'],
                (521, 178))
        self.set_image_sizes()

        self.setup_variables()

    def setup_variables(self):
        """Sets up the variables."""
        self.airspace = Airspace(self.size[0]*7/16, self.size[1]/24,
                self.size[0]*35/64, self.size[1]*35/48)
        self.plane = self.airspace.add_plane(self.images['navmarker'],
                player_id=self.id)
        self.planes = self.airspace.planes # Another name for the same object
        self.objectives = self.airspace.objectives
        self.airspace.generate_objective(self.images['objectivemarker'])
        for obj in self.objectives: self.closest_objective = obj

        self.btn_units = utils.Button(self.size[0]*5/256, self.size[1]*5/96,
                self.size[0] / 8, self.size[0] / 36, "Units: SI",
                color=self.colors['panel'], color_outline=None,
                color_text=self.colors['white'], font_size=24)

        self.stage = 0
        self.paused = 0
        self.ignore_warnings = 1
        self.status = ["Fly to the objective."]
        self.exit_code = 0
        self.warnings = {
            "terrain": False,
            "terrainloop": False,
            "terrain-toggle": False,
            "pullup": False,
            "pulluploop": False,
            "pullup-toggle": False,
            "pulluploop2": False,
            "pullup-toggle2": False,
            "dontsink": False,
            "dontsinkloop": False,
            "dontsink-toggle": False,
            "overspeed": False,
            "bankangle": False,
            "altitude": False,
            "stall": False
        }

        self.output_log = True
        self.startup_time = time.time()
        self.previous_time = time.time()
        self.time = time.time()
        self.tick = 0

        self.event_log = pygame.USEREVENT
        pygame.time.set_timer(self.event_log, 5000)
        self.event_warn = pygame.USEREVENT + 1
        pygame.time.set_timer(self.event_warn, 1000)
        self.event_toggletext = pygame.USEREVENT + 2
        pygame.time.set_timer(self.event_toggletext, 333)

    def set_image_sizes(self):
        """Sets up the images."""
        for image_name in self.images:
            x, y = self.images[image_name].get_rect().size
            x *= (self.size[0] / self.DEFAULT_SIZE[0])
            y *= (self.size[1] / self.DEFAULT_SIZE[1])
            x = int(x); y = int(y)
            self.images[image_name] = pygame.transform.scale(
                    self.images[image_name], (x, y))

    def prepare_log(self):
        """Prepares the log."""
        self.log_filepath = "%s/logs/%s.log" % (PATH, datetime.datetime.now())
        self.log_file = open(self.log_filepath, 'wt')
        output = []
        # first row labels
        output.append("TIME\t\t\t")
        for plane_id in range(len(self.planes)):
            output.append("PLN-%i\t\t\t\t\t\t\t\t\t\t\t\t" % plane_id)
        for objective_id in range(len(self.objectives)):
            output.append("OBJ-%i\t\t\t" % objective_id)
        # second row labels
        output.append("\nSEC:\tTICK:\tDUR:\t")
        for plane_id in range(len(self.planes)):
            for plane in self.planes:
                if plane.id == plane_id: break
            output.append(plane.labels())
        for objective_id in range(len(self.objectives)):
            for objective in self.objectives:
                if objective.id == objective_id: break
            output.append(objective.labels())
        self.log_file.write(''.join(output))
        self.log_file.write('\n')
        if self.output_log:
            print('====== START LOG ======')
            print(''.join(output))
        self.log_file.close()

    # -------------------------------------------------------------------------
    # FUNCTIONS
    # -------------------------------------------------------------------------

    def update_screen_size(self, new_size):
        """Updates the screen size."""
        self.prev_size = self.size
        new_size = list(new_size)
        if self.size[0] == self.prev_size[0]:
            new_size[0] = self.size[0] * (self.size[1] / self.prev_size[1])
        if self.size[1] == self.prev_size[1]:
            new_size[1] = self.size[1] * (self.size[0] / self.prev_size[0])
        self.screen = pygame.display.set_mode(new_size, pygame.RESIZABLE)
        self.size = new_size
        self.scale_images()

    def scale_images(self):
        """Sets up the images."""
        for image_name in self.images:
            x, y = self.images[image_name].get_rect().size
            x *= (self.size[0] / self.prev_size[0])
            y *= (self.size[1] / self.prev_size[1])
            x = int(x); y = int(y)
            self.images[image_name] = pygame.transform.scale(
                    self.images[image_name], (x, y))

    def draw(self):
        """Draws the info box and airspace."""
        # get closest objective
        closest_dist = float('inf')
        for obj in self.objectives:
            dist = ((self.plane.rect.x - obj.rect.x) ** 2
                    + (self.plane.rect.y - obj.rect.y) ** 2) ** 0.5
            if dist < closest_dist:
                closest_dist = dist
                closest_objective = obj
        self.closest_objective = closest_objective
            
        # attitude tape
        attitude_tape = pygame.transform.rotate(
                self.images['attitudetape-bg'], self.plane.roll_degrees)
        attitude_tape_rect = attitude_tape.get_rect()
        attitude_tape_rect.center = (self.size[0]*55/256,
                self.size[1]*9/24)
        offset_total = (attitude_tape_rect.height * 3/1600 * self.size[1]
                /attitude_tape_rect.height * self.plane.pitch_degrees)
        offset_x = math.sin(self.plane.roll) * offset_total
        offset_y = math.cos(self.plane.roll) * offset_total
        attitude_tape_rect.x += offset_x
        attitude_tape_rect.y += offset_y

        attitude_tape_overlay = pygame.transform.rotate(
                self.images['attitudetape-overlay'], self.plane.roll_degrees)
        attitude_tape_overlay_rect = attitude_tape_overlay.get_rect()
        attitude_tape_overlay_rect.center = (self.size[0]*55/256,
                self.size[1]*9/24)
        offset_total = (attitude_tape_overlay_rect.height*3/1600*self.size[1]
                /attitude_tape_overlay_rect.height * self.plane.pitch_degrees)
        offset_x = math.sin(self.plane.roll) * offset_total
        offset_y = math.cos(self.plane.roll) * offset_total
        attitude_tape_overlay_rect.x += offset_x
        attitude_tape_overlay_rect.y += offset_y
        self.screen.blit(attitude_tape, attitude_tape_rect)
        self.screen.blit(attitude_tape_overlay, attitude_tape_overlay_rect)
        # surrounding panels
        pygame.draw.rect(self.screen, self.colors['panel'],
                (self.size[0]*5/256, self.size[1]*5/48,
                self.size[0]*25/64, self.size[1]*7/48))
        pygame.draw.rect(self.screen, self.colors['panel'],
                (self.size[0]*5/256, self.size[1]*5/48,
                self.size[0]*15/128, self.size[1]*25/48))
        pygame.draw.rect(self.screen, self.colors['panel'],
                (self.size[0]*75/256, self.size[1]*5/48,
                self.size[0]*15/128, self.size[1]*25/48))
        pygame.draw.rect(self.screen, self.colors['panel'],
                (self.size[0]*5/256, self.size[1]/2,
                self.size[0]*25/64, self.size[1]*7/48))
        self.screen.blit(self.images['attitudecrosshair'],
                (self.size[0]*35/256, self.size[1]*9/24))

        # redraw background
        pygame.draw.rect(self.screen, self.colors['background'],
                (0, 0, self.size[0], self.size[1]*5/48))
        pygame.draw.rect(self.screen, self.colors['background'],
                (0, 0, self.size[0]*5/256, self.size[1]))
        pygame.draw.rect(self.screen, self.colors['background'],
                (0, self.size[1]*15/24, self.size[0], self.size[1]*9/24))
        pygame.draw.rect(self.screen, self.colors['background'],
                (self.size[0]*105/256, 0, self.size[0]*151/256, self.size[1]))

        # draw NAV/airspace
        self.airspace.draw(self.screen, self.images['navcircle'],
                self.colors['black'], self.colors['panel'])
        
        # NAV text
        self.draw_text("PLANE LOCATION", self.size[0]*29/64, self.size[1]/16,
                color_id='white', mode='topleft')
        self.draw_text("X: %%.%if" % UNITS[self.unit_id]['pos']['round-to']
                % (self.plane.ux * UNITS[self.unit_id]['pos']['value']),
                self.size[0]*29/64, self.size[1]/12,
                color_id='white', mode='topleft')
        self.draw_text("Z: %%.%if" % UNITS[self.unit_id]['pos']['round-to']
                % (self.plane.uz * UNITS[self.unit_id]['pos']['value']),
                self.size[0]*29/64, self.size[1]*5/48,
                color_id='white', mode='topleft')
        self.draw_text("ALT: %%.%if %%s" % UNITS[self.unit_id]['pos']['round-to']
                % (self.plane.altitude * UNITS[self.unit_id]['pos']['value'],
                UNITS[self.unit_id]['pos']['name']),
                self.size[0]*29/64, self.size[1]/8,
                color_id='white', mode='topleft')
        self.draw_text("HEADING: %.1f°" % self.plane.heading_degrees,
                self.size[0]*91/128, self.size[1]/16,
                color_id='white', mode='midtop')
        self.draw_text("PITCH: %.1f°" % self.plane.pitch_degrees,
                self.size[0]*91/128, self.size[1]/12,
                color_id='white', mode='midtop')
        self.draw_text("SCORE: %i" % self.plane.points,
                self.size[0]*91/128, self.size[1]*5/48,
                color_id='white', mode='midtop')
        self.draw_text("OBJECTIVE LOCATION", self.size[0]*31/32, self.size[1]/16,
                color_id='white', mode='topright')
        self.draw_text("X: %%.%if" % UNITS[self.unit_id]['pos']['round-to']
                % (closest_objective.ux * UNITS[self.unit_id]['pos']['value']),
                self.size[0]*31/32, self.size[1]/12,
                color_id='white', mode='topright')
        self.draw_text("Z: %%.%if" % UNITS[self.unit_id]['pos']['round-to']
                % (closest_objective.uz * UNITS[self.unit_id]['pos']['value']),
                self.size[0]*31/32, self.size[1]*5/48,
                color_id='white', mode='topright')
        self.draw_text("ALT: %%.%if %%s" % UNITS[self.unit_id]['pos']['round-to']
                % (closest_objective.altitude
                * UNITS[self.unit_id]['pos']['value'],
                UNITS[self.unit_id]['pos']['name']),
                self.size[0]*31/32, self.size[1]/8,
                color_id='white', mode='topright')

        # panel text
        self.draw_text("THROTTLE", self.size[0]*3/128, self.size[1]/4,
                color_id='white', mode='topleft')
        self.draw_text("%.1f%%" % self.plane._throttle,
                self.size[0]*3/128, self.size[1]*13/48,
                color_id='white', mode='topleft')
        self.draw_text("GRAVITY", self.size[0]*3/128, self.size[1]*17/48,
                color_id='white', mode='topleft')
        self.draw_text("%%.%if %%s" % UNITS[self.unit_id]['speed']['round-to']
                % (-self.plane.gravity * UNITS[self.unit_id]['speed']['value'],
                UNITS[self.unit_id]['speed']['name']),
                self.size[0]*3/128, self.size[1]*3/8,
                color_id='white', mode='topleft')
        self.draw_text("DAMAGE", self.size[0]*3/128, self.size[1]*11/24,
                color_id='white', mode='topleft')
        self.draw_text("%.1f%%" % (100 - self.plane.health),
                self.size[0]*3/128, self.size[1]*23/48,
                color_id='white', mode='topleft')
        self.draw_text("SPEED", self.size[0]*5/16, self.size[1]/4,
                color_id='white', mode='topleft')
        self.draw_text("%%.%if %%s" % UNITS[self.unit_id]['speed']['round-to']
                % (self.plane.speed * UNITS[self.unit_id]['speed']['value'],
                UNITS[self.unit_id]['speed']['name']),
                self.size[0]*5/16, self.size[1]*13/48,
                color_id='white', mode='topleft')
        self.draw_text("HORIZ SPD", self.size[0]*5/16, self.size[1]*17/48,
                color_id='white', mode='topleft')
        self.draw_text("%%.%if %%s" % UNITS[self.unit_id]['speed']['round-to']
                % (self.plane.horizontal_speed
                * UNITS[self.unit_id]['speed']['value'],
                UNITS[self.unit_id]['speed']['name']),
                self.size[0]*5/16, self.size[1]*3/8,
                color_id='white', mode='topleft')
        self.draw_text("VERT SPD", self.size[0]*5/16, self.size[1]*11/24,
                color_id='white', mode='topleft')
        self.draw_text("%%.%if %%s" % UNITS[self.unit_id]['speed']['round-to']
                % (self.plane.vertical_velocity
                * UNITS[self.unit_id]['speed']['value'],
                UNITS[self.unit_id]['speed']['name']),
                self.size[0]*5/16, self.size[1]*23/48,
                color_id='white', mode='topleft')

        # throttle bar
        pygame.draw.rect(self.screen, self.colors['red'],
                (self.size[0]*15/128, self.size[1]*76/192,
                self.size[0]/64, self.size[1]*5/192))
        pygame.draw.rect(self.screen, self.colors['white'],
                (self.size[0]*15/128, self.size[1]*81/192,
                self.size[0]/64, self.size[1]*15/192))
        pygame.draw.rect(self.screen, self.colors['green'],
                (self.size[0]*15/128,
                self.size[1]/self.DEFAULT_SIZE[1]*(480-self.plane._throttle),
                self.size[0]/64,
                self.size[1]/self.DEFAULT_SIZE[1]*self.plane._throttle))

        # status
        for line_id in range(len(self.status)):
            self.draw_text(self.status[line_id],
                    self.size[0]*5/256, self.size[1]*(21/32+1/24*line_id),
                    font_id="large", color_id='white', mode='topleft')

        # warnings
        if self.warnings["pullup"] and not self.ignore_warnings:
            self.screen.blit(self.images['msg_pullup'],
                    (self.size[0]*5/32, self.size[1]*49/96))
        if self.warnings["terrain"] and not self.ignore_warnings:
            self.screen.blit(self.images['msg_warning'],
                    (self.size[0]*187/1280, self.size[1]*7/40))
        if self.warnings["stall"]:
            self.screen.blit(self.images['msg_stall'],
                    (self.size[0]*33/1280, self.size[1]*491/960))
        if self.warnings["dontsink"] and not self.ignore_warnings:
            self.screen.blit(self.images['msg_dontsink'],
                    (self.size[0]*19/80, self.size[1]*109/192))
        if self.warnings["bankangle"]:
            self.screen.blit(self.images['msg_bankangle'],
                    (self.size[0]/40, self.size[1]*109/192))
        if self.warnings["overspeed"]:
            self.screen.blit(self.images['msg_overspeed'],
                    (self.size[0]*73/256, self.size[1]*49/96))
        # autopilot message
        if self.plane.ap_enabled:
            self.screen.blit(self.images['msg_apengaged'],
                    (self.size[0]*17/128, self.size[1]*11/96))
        else:
            self.screen.blit(self.images['msg_apdisconnect'],
                    (self.size[0]*7/64, self.size[1]*11/96))

        # buttons
        self.btn_units.draw(self.screen)

    def control_plane(self):
        """Allows you to control the plane."""
        if not self.plane.ap_enabled:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.key_held[0] += 1
                self.plane.roll_level -= ((self.key_held[0] / 3) ** .75 / self.fps)
                if self.plane.roll_level < -4: self.plane.roll_level = -4
            elif keys[pygame.K_RIGHT]:
                self.key_held[0] += 1
                self.plane.roll_level += ((self.key_held[0] / 3) ** .75 / self.fps)
                if self.plane.roll_level > 4: self.plane.roll_level = 4
            else: self.key_held[0] = 0
            if keys[pygame.K_UP]:
                self.key_held[1] += 1
                self.plane.vertical_roll_level -= ((self.key_held[1] / 3) ** .75 / self.fps)
                if self.plane.vertical_roll_level < -4:
                    self.plane.vertical_roll_level = -4
            elif keys[pygame.K_DOWN]:
                self.key_held[1] += 1
                self.plane.vertical_roll_level += ((self.key_held[1] / 3) ** .75 / self.fps)
                if self.plane.vertical_roll_level > 4:
                    self.plane.vertical_roll_level = 4
            else: self.key_held[1] = 0
            if keys[pygame.K_F2]:
                self.key_held[2] += 1
                self.plane._throttle -= ((self.key_held[2] / 3) ** .75 / self.fps)
                if self.plane._throttle < 0: self.plane._throttle = 0
            elif keys[pygame.K_F4]:
                self.key_held[2] += 1
                self.plane._throttle += ((self.key_held[2] / 3) ** .75 / self.fps)
                if self.plane._throttle > 100: self.plane._throttle = 100
            else: self.key_held[2] = 0

            for event in self.events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1: self.plane._throttle = 0
                    elif event.key == pygame.K_F3: self.plane._throttle = 25
                    elif event.key == pygame.K_F5: self.plane._throttle = 75
                    elif event.key == pygame.K_z: self.plane.ap_enabled = True

    def run_warnings(self):
        """Runs warnings."""
        if self.warnings["pullup"] and not self.ignore_warnings:
            self.sounds['pullup'].play()
            self.warnings["pullup"] = False
        elif self.warnings["terrain"] and not self.ignore_warnings:
            self.sounds['terrain'].play()
            self.warnings["terrain"] = False
        elif self.warnings["stall"]:
            self.sounds['stall'].play()
            self.warnings["stall"] = False
        elif self.warnings["dontsink"] and not self.ignore_warnings:
            self.sounds['dontsink'].play()
            self.warnings["dontsink"] = False
        if self.warnings["bankangle"]:
            self.sounds['bankangle'].play()
            self.warnings["bankangle"] = False
        if self.warnings["overspeed"]:
            self.sounds['overspeed'].play()
            self.warnings["overspeed"] = False
        if self.warnings["altitude"]:
            self.sounds['altitude'].play()
            self.warnings["altitude"] = False
        if self.warnings["pulluploop"]:
            if self.warnings["pullup-toggle"]:
                self.warnings["pullup"] = True
                self.warnings["pullup-toggle"] = False
            else:
                self.warnings["pullup-toggle"] = True
        if self.warnings["pulluploop2"]:
            if self.warnings["pullup-toggle2"]:
                self.warnings["pullup"] = True
                self.warnings["pullup-toggle2"] = False
            else:
                self.warnings["pullup-toggle2"] = True
        if self.warnings["terrainloop"]:
            if self.warnings["terrain-toggle"]:
                self.warnings["terrain"] = True
                self.warnings["terrain-toggle"] = False
            else:
                self.warnings["terrain-toggle"] = True
        if self.warnings["dontsinkloop"]:
            if self.warnings["dontsink-toggle"]:
                self.warnings["dontsink"] = True
                self.warnings["dontsink-toggle"] = False
            else:
                self.warnings["dontsink-toggle"] = True

    def log(self, text=None):
        """Writes in the log.

        The log logs every 5 seconds.  It records:
         - The game tick that the log is recording at
         - How many milliseconds long that tick was
         - The coordinates, heading and score of all planes
         - The coordinates of all objectives
        If the argument text is specified, logs that instead.
        """
        self.log_file = open(self.log_filepath, 'at')
        if text == None:
            output = []
            output.append("%.1f\t%i\t%i\t" % ((self.time-self.startup_time),
                    self.tick, (self.time-self.previous_time) * 1000))
            # outputs stats in the correct order
            for plane_id in range(len(self.planes)):
                for plane in self.planes:
                    if plane.id == plane_id: break
                output.append(plane.__repr__(False))
            for objective_id in range(len(self.objectives)):
                for objective in self.objectives:
                    if objective.id == objective_id: break
                output.append(objective.__repr__(False))
        else: output = text
        self.log_file.write(''.join(output))
        self.log_file.write('\n')
        if self.output_log: print(''.join(output))
        self.log_file.close()

    def get_tick_values(self):
        """Prepares the values for the log."""
        self.tick += 1
        self.previous_time = self.time
        self.time = time.time()  

    # -------------------------------------------------------------------------
    # MAIN LOOP
    # -------------------------------------------------------------------------

    def game_loop(self):
        """One iteration of the main loop.

        (In reality, just runs one of the game loops)"""
        self.GAME_LOOPS[self.stage] (self)
        pygame.display.flip()
        for event in self.events:
            if event.type == pygame.QUIT or self.stage == 'END':
                return True
            elif event.type == pygame.VIDEORESIZE:
                self.update_screen_size(event.size)
            
    def startup_screen(self):
        """Activates the startup screen. Stage=0"""
        pygame.mixer.music.stop()
        pygame.mixer.music.load(self.music_files['chilled-eks'])
        pygame.mixer.music.play(-1)
    def game_loop_startup(self):
        """One iteration of the startup screen loop."""
        self.screen.blit(self.images['logo'], ((self.size[0]
                - self.images['logo'].get_width()) / 2,
                self.size[1]/18.8))
        self.screen.blit(self.images['logotext'], ((self.size[0]
                - self.images['logotext'].get_width()) / 2, self.size[1]/2.4))
        self.screen.blit(self.images['titleprompt'], (self.size[0]*35/64,
                self.size[1]*35/48))
        pygame.display.flip()
        for event in self.events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.stage = 1
                elif event.key == pygame.K_ESCAPE:
                    self._stage = 'END'
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.stage = 1
    GAME_STAGES[0] = startup_screen
    GAME_LOOPS[0] = game_loop_startup

    def main_screen(self):
        """Activates the main screen. Stage=1"""
        pygame.mixer.music.stop()
        pygame.mixer.music.load(self.music_files['chip-respect'])
        pygame.mixer.music.play(-1)
        self.prepare_log()
        self.log()
    def game_loop_main(self):
        """One iteration of the main loop."""
        if not self.paused:
            self.control_plane()
            self.airspace.update(self)
            self.draw()
        elif self.paused != 1:
            self.draw()
            self.draw_text("PAUSED", self.airspace.center,
                    color_id='white', font_id='large')
        else:
            self.draw()
        if self.plane.exit_code != 0:
            self.log("[!] Exited main loop with exitcode %i"
                    % self.plane.exit_code)
            self.exit_title = self.EXIT_TITLES[self.plane.exit_code]
            self.exit_reason = self.EXIT_REASONS[self.plane.exit_code]
            if self.plane.exit_code not in [0, 7]:
                self.exit_reason %= self.plane.points
            self.exit_code = self.plane.exit_code
            self.stage = 2
        pygame.display.flip()
        for event in self.events:
            if event.type == pygame.QUIT:
                self.plane.exit_code = 2
                self.events.remove(event)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.paused:
                        self.log("[!] Player unpaused")
                        self.paused = 0
                    else:
                        self.log("[!] Player paused")
                        self.paused = 1
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.btn_units.is_pressed():
                    self.unit_id += 1
                    if self.unit_id >= len(UNITS):
                        self.unit_id = 0
                    self.btn_units.text = "Units: %s" % UNITS[self.unit_id]['name']
            elif event.type == self.event_log and not self.paused:
                self.log()
            elif event.type == self.event_warn:
                self.run_warnings()
            elif event.type == self.event_toggletext:
                if self.paused:
                    self.paused += 1
                    if self.paused >= 4: self.paused = 1
        self.get_tick_values()
    GAME_STAGES[1] = main_screen
    GAME_LOOPS[1] = game_loop_main

    def end_screen(self):
        """Activates the end screen. Stage=2"""
        pygame.mixer.music.fadeout(10000) # Fades out over 10 seconds
        self.status = "You may now close the program."
    def game_loop_end(self):
        """One iteration of the end screen loop."""
        self.draw_text(self.exit_title,
                (self.size[0]/37.6, self.size[0]/48),
                mode='topleft', color_id='white', font_id='large')
        self.draw_text(self.exit_reason,
                (self.size[0]/37.6, self.size[1]*5/48),
                mode='bottomleft', color_id='white')
        self.draw_text(self.status, (self.size[0]/37.6, self.size[1]*35/48),
                mode='topleft', color_id="white")

        pygame.display.flip()
    GAME_STAGES[2] = end_screen
    GAME_LOOPS[2] = game_loop_end

    @property
    def stage(self):
        """Allows you to get the stage."""
        return self._stage
    @stage.setter
    def stage(self, new_value):
        """Allows you to set the stage variable to change the stage."""
        self.GAME_STAGES[new_value] (self)
        self._stage = new_value
