#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""The main game code

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
Just a bit of fimulating

UNITS USED INTERNALLY

Speed: m/s and km/h
1 m/s = 3.6 km/h = 1.94384 KTS
1 KTS = 1.852 km/h = 0.514444 m/s
1 km/h = 0.277778 m/s = 0.539957 KTS

Vert. Speed: m/s and km/h
1 m/s = 3.28084 ft/s
1 ft/s = 0.3048 m/s

Distance: m, km
1 km = 1000 m = 0.539957 NM
1 NM = 1.852 km = 1852 m

Height: m
1 m = 3.28084 ft
1 ft = 0.3048 m
"""

# Installs Python 3 division behaviour
from __future__ import division

import datetime
import math
import os
import random
import time

import pygame

import unofficial_utilities_for_pygame as utils
from __init__ import __author__, __credits__, __version__
from constants import *

PATH = os.path.dirname(os.path.realpath(__file__))


class Airplane(utils.ImprovedSprite):
    """The class for an airplane sprite."""
    NEXT_ID = 0
    def __init__(self, image, x=(0, 0, 0), y=None, altitude=None,
            speed=440, throttle=50, player_id=None, airspace_dim=[700, 700]):
        """Initializes the instance."""
        if y == None and altitude != None: x, y = x
        elif y == None: x, y, altitude = x
        super(Airplane, self).__init__(image, x, y)
        self.pos = list(self.rect.center)
        self.upos = self.pos[:]
        self.upos[0] *= (1000.0/airspace_dim[0])
        self.upos[1] *= (1000.0/airspace_dim[1])
        self.altitude = altitude
        self.heading = 0
        self.pitch = 0
        self.speed = speed # m/s
        self.horizontal_velocity = speed
        self.vertical_velocity = 0
        self.max_vert_roll = 0
        self.gravity_force = -360
        self.gravity = -360
        self.throttle = throttle
        self.acceleration = 0 # m/s^2
        self.roll_level = 0
        self.roll = 0
        self.vertical_roll_level = 0
        self.ap_cond = [1, 1, 1]
        self.ap_enabled = False

        self.within_objective_range = False
        self.points = 0
        self.exit_code = 0
        self.health = 100
        self.warnings = []
        if player_id == None: self.id = Airplane.NEXT_ID; Airplane.NEXT_ID += 1
        else: self.id = player_id

    def draw(self, screen, airspace_x, airspace_y=None):
        """Draws the airplane."""
        if airspace_y == None: airspace_x, airspace_y = airspace_x
        image_rotated = pygame.transform.rotate(self.image, -self.heading)
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
        self.roll = self.get_roll(self.roll_level)
        self.heading += (self.roll / window.fps)
        if self.heading <= 0: self.heading += 360
        elif self.heading > 360: self.heading -= 360
        if self.vertical_roll_level > self.max_vert_roll:
            self.vertical_roll_level = self.max_vert_roll
        self.pitch = self.get_vert_hd(self.vertical_roll_level)

        # acceleration
        self.acceleration = (self.throttle ** 2 / 78.125
                - self.speed ** 2 / 6050)
        self.speed += (self.acceleration / float(window.fps))
        self.horizontal_speed = self.speed * math.cos(math.radians(
                self.pitch))
        self.vertical_velocity = self.speed * math.sin(math.radians(
                self.pitch))

        # apply gravity if going too slow
        if self.speed <= 176:
            window.warnings['stall'] = True
            self.max_vert_roll = max((self.speed-88) / 22, 0)
        else: self.max_vert_roll = 4
        self.gravity_force += (((88 - self.speed) / 88 * 32)
                - (self.gravity_force ** 2 / 3200)) / window.fps
        if self.gravity_force < 0: self.gravity_force = 0
        self.gravity = self.gravity_force
        self.total_vertical_velocity = self.vertical_velocity - self.gravity
        
        hspeed = self.horizontal_speed / window.fps
        vspeed = self.total_vertical_velocity / window.fps
        self.pos[0] += math.sin(math.radians(self.heading)) * hspeed * x_str
        self.pos[1] -= math.cos(math.radians(self.heading)) * hspeed * y_str
        self.rect.center = tuple(self.pos)
        self.altitude += vspeed

        # User-freindly coordinates
        # Goes from 0 to +1000 in both dimensions
        self.upos = self.pos[:]
        self.upos[0] *= (1/x_str)
        self.upos[1] *= (1/y_str)

        # overspeed damage
        if self.speed > 880:
            window.warnings['overspeed'] = True
            damage += (self.speed - 880) ** 2 / 60500 / window.fps
        if self.throttle > 100:
            damage += (self.throttle - 100) ** 2 / 781.25 / window.fps

        # height warnings
        if self.altitude <= 1600:
            window.warnings['pulluploop'] = True
            window.status = ["PRESS AND HOLD", "THE \"DOWN\" KEY!"]
        elif (self.altitude < 3200 and self.vertical_velocity > 0
                and self.throttle < 50):
            window.warnings['dontsinkloop'] = True
            window.status = ["Be careful not to stall."]
        elif (self.altitude < 3200 and self.speed > 800):
            window.warnings["terrainloop"] = True
        elif (self.altitude < 3200 and self.speed <= 800):
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
        else:
            self.within_objective_range = False
            window.status = ["Fly to the objective."]

        if abs(self.roll) >= 30:
            window.warnings['bankangle'] = True

        # disable loops
        if not (self.altitude < 3200 and self.vertical_velocity > 0
                and self.throttle < 50):
            window.warnings['dontsinkloop'] = False
        if not (self.altitude < 3200 and self.speed > 800):
            window.warnings["terrainloop"] = False
        if not (self.altitude < 3200 and self.speed <= 800):
            window.warnings['pulluploop2'] = False

        # autopilot
        if self.ap_enabled:
            self.roll_level *= (0.5 ** (1.0/window.fps))
            self.vertical_roll_level *= (0.5 ** (1.0/window.fps))
            self.throttle = 50 + (self.throttle-50) * (0.5 ** (1.0/window.fps))
            window.status = ["Autopilot engaged..."]
            if abs(self.roll_level) < 0.1:
                self.roll_level = 0
                self.ap_cond[0] = True
            else: self.ap_cond[0] = False
            if abs(self.vertical_roll_level) < 0.1:
                self.vertical_roll_level = 0
                self.ap_cond[1] = True
            else: self.ap_cond[0] = False
            if abs(50 - self.throttle) < 1:
                self.throttle = 50
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
        elif self.points >= POINTS_REQUIRED:
            self.exit_code = 1

        # position-related exit
        if self.altitude > MAX_ALTITUDE:
            self.exit_code = 6
        elif self.altitude <= 0:
            self.exit_code = 3
        elif not window.airspace.in_bounds(self):
            self.exit_code = 4

    # Function that approximates the 5, 10, 20, 30 roll of Slight Fimulator 1.0
    get_roll = lambda s, r: (35/198.0) * r**3 + (470/99.0) * r
    get_vert_hd = lambda s, r: 10*r


class Objective(utils.ImprovedSprite):
    """The class for an objective sprite."""
    NEXT_ID = 0
    def __init__(self, image, x=(0, 0, 0), y=None, altitude=None, obj_id=None,
            airspace_dim=[700, 700]):
        """Initializes the instance."""
        if y == None and altitude != None: x, y = x
        elif y == None: x, y, altitude = x
        super(Objective, self).__init__(image, x, y)
        self.altitude = altitude

        if obj_id == None: self.id = Objective.NEXT_ID; Objective.NEXT_ID += 1
        else: self.id = obj_id

        self.upos = list(self.rect.center[:])
        self.upos[0] -= airspace_dim[0] / 2
        self.upos[0] *= (2*AIRSPACE_DIM/airspace_dim[0])
        self.upos[1] -= airspace_dim[1] / 2
        self.upos[1] *= (2*AIRSPACE_DIM/airspace_dim[1])

    def draw(self, screen, airspace_x, airspace_y=None):
        """Draws the objective."""
        if airspace_y == None: airspace_x, airspace_y = airspace_x
        draw_rect = self.rect.copy()
        draw_rect.x += airspace_x
        draw_rect.y += airspace_y
        screen.blit(self.image, draw_rect)

    def update(self, window):
        """Updates the objective."""
        self.upos = list(self.rect.center[:])
        self.upos[0] *= (AIRSPACE_DIM/window.airspace.width)
        self.upos[1] *= (AIRSPACE_DIM/window.airspace.height)


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

        Creates a new airplane if an image is supplied."""
        if type(plane) != Airplane:
            plane = Airplane(plane, self.width/2, self.height/2,
                    START_ALTITUDE, airspace_dim=self.size,
                    player_id=player_id)
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
            objective.rect.centerx = random.randint(0, self.width)
            objective.rect.centery = random.randint(0, self.height)
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
        if player_id == None: self.id = Game.NEXT_ID; Game.NEXT_ID += 1
        else: self.id = player_id

    # -------------------------------------------------------------------------
    # STARTUP CODE
    # -------------------------------------------------------------------------

    def startup(self):
        """A function that is run once on startup."""
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()
##        # Makes the screen resizable
##        self.screen = pygame.display.set_mode(self.size, pygame.RESIZABLE)

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

        self.stage = 0
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
        self.previous_time = time.time()
        self.time = time.time()
        self.tick = 0

        self.event_log = pygame.USEREVENT
        pygame.time.set_timer(self.event_log, 5000)
        self.event_warn = pygame.USEREVENT + 1
        pygame.time.set_timer(self.event_warn, 1000)

    def set_image_sizes(self):
        """Sets up the images."""
        for image_name in self.images:
            x, y = self.images[image_name].get_rect().size
            x *= (self.size[0] / float(self.DEFAULT_SIZE[0]))
            y *= (self.size[1] / float(self.DEFAULT_SIZE[1]))
            x = int(x); y = int(y)
            self.images[image_name] = pygame.transform.scale(
                    self.images[image_name], (x, y))

    def prepare_log(self):
        """Prepares the log."""
        self.log_filepath = "%s/logs/%s.log" % (PATH, datetime.datetime.now())
        self.log_file = open(self.log_filepath, 'wt')
        output = []
        output.append("TIME\t\t")
        for plane_id in range(len(self.planes)):
            output.append("PLN-%i\t\t\t\t\t\t\t\t\t\t\t\t\t\t" % plane_id)
        for objective_id in range(len(self.objectives)):
            output.append("OBJ-%i\t\t\t" % objective_id)
        output.append("\nTICK:\tDUR:\t")
        for plane_id in range(len(self.planes)):
            output.append(
"X:\tY:\tALT:\tSPD:\tACCEL:\tCLIMB:\tTHR:\t\
HDG:\tPITCH:\tCR:\tROLL:\tVCR:\tPTS:\tDMG:\t")
        for objective_id in range(len(self.objectives)):
            output.append("X:\tY:\tALT:\t")
        self.log_file.write(''.join(output))
        self.log_file.write('\n')
        if self.output_log:
            print('======START LOG======')
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
            x *= (self.size[0] / float(self.prev_size[0]))
            y *= (self.size[1] / float(self.prev_size[1]))
            x = int(x); y = int(y)
            self.images[image_name] = pygame.transform.scale(
                    self.images[image_name], (x, y))

    def draw(self):
        """Draws the info box and airspace."""
        for plane in self.planes:
            if plane.id == 0: break
        # get closest objective
        closest_dist = float('inf')
        for obj in self.objectives:
            dist = ((plane.rect.x - obj.rect.x) ** 2
                    + (plane.rect.y - obj.rect.y) ** 2) ** 0.5
            if dist < closest_dist:
                closest_dist = dist
                closest_objective = obj
        self.closest_objective = closest_objective
            
        # attitude tape
        attitude_tape = pygame.transform.rotate(
                self.images['attitudetape-bg'], self.plane.roll)
        attitude_tape_rect = attitude_tape.get_rect()
        attitude_tape_rect.center = (self.size[0]*55/256,
                self.size[1]*9/24)
        offset_total = (attitude_tape_rect.height * 3/1600 * self.size[1]
                /attitude_tape_rect.height * self.plane.pitch)
        offset_x = math.sin(math.radians(self.plane.roll)) * offset_total
        offset_y = math.cos(math.radians(self.plane.roll)) * offset_total
        attitude_tape_rect.x += offset_x
        attitude_tape_rect.y += offset_y

        attitude_tape_overlay = pygame.transform.rotate(
                self.images['attitudetape-overlay'], self.plane.roll)
        attitude_tape_overlay_rect = attitude_tape_overlay.get_rect()
        attitude_tape_overlay_rect.center = (self.size[0]*55/256,
                self.size[1]*9/24)
        offset_total = (attitude_tape_overlay_rect.height*3/1600*self.size[1]
                /attitude_tape_overlay_rect.height * self.plane.pitch)
        offset_x = math.sin(math.radians(self.plane.roll)) * offset_total
        offset_y = math.cos(math.radians(self.plane.roll)) * offset_total
        attitude_tape_overlay_rect.x += offset_x
        attitude_tape_overlay_rect.y += offset_y
        self.screen.blit(attitude_tape, attitude_tape_rect)
        self.screen.blit(attitude_tape_overlay, attitude_tape_overlay_rect)
        # surrounding panel
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

        # vertical speed tape
        verticalspeedrect = pygame.rect.Rect(self.size[0]*75/256,
                self.size[1]*73/192, self.size[0]/64,
                self.size[1]/self.DEFAULT_SIZE[1]*-plane.vertical_velocity/10)
        if plane.vertical_velocity < 0:
            verticalspeedrectcolor = self.colors['red']
        elif plane.vertical_velocity > 0:
            verticalspeedrectcolor = self.colors['green']
        else:
            verticalspeedrectcolor = self.colors['white']
        
        pygame.draw.rect(self.screen, verticalspeedrectcolor,
                verticalspeedrect)
        
        # NAV text
        self.draw_text("PLANE LOCATION",
                self.size[0]*29/64, self.size[1]/16,
                color_id='white', mode='topleft')
        self.draw_text("X: %.2f" % (plane.upos[0] / 6076),
                self.size[0]*29/64, self.size[1]/12,
                color_id='white', mode='topleft')
        self.draw_text("Y: %.2f" % (plane.upos[1] / 6076),
                self.size[0]*29/64, self.size[1]*5/48,
                color_id='white', mode='topleft')
        self.draw_text("ALT: %i FT" % plane.altitude,
                self.size[0]*29/64, self.size[1]/8,
                color_id='white', mode='topleft')
        self.draw_text("HEADING: %.1f" % plane.heading,
                self.size[0]*91/128, self.size[1]/16,
                color_id='white', mode='midtop')
        self.draw_text("PITCH: %.1f" % plane.pitch,
                self.size[0]*91/128, self.size[1]/12,
                color_id='white', mode='midtop')
        self.draw_text("SCORE: %i" % plane.points,
                self.size[0]*91/128, self.size[1]*5/48,
                color_id='white', mode='midtop')
        self.draw_text("OBJECTIVE LOCATION",
                self.size[0]*31/32, self.size[1]/16,
                color_id='white', mode='topright')
        self.draw_text("X: %.2f" % (closest_objective.upos[0] / 6076),
                self.size[0]*31/32, self.size[1]/12,
                color_id='white', mode='topright')
        self.draw_text("Y: %.2f" % (closest_objective.upos[1] / 6076),
                self.size[0]*31/32, self.size[1]*5/48,
                color_id='white', mode='topright')
        self.draw_text("ALT: %i FT" % closest_objective.altitude,
                self.size[0]*31/32, self.size[1]/8,
                color_id='white', mode='topright')

        # panel text
        self.draw_text("THROTTLE",
                self.size[0]*3/128, self.size[1]/4,
                color_id='white', mode='topleft')
        self.draw_text("%.1f%%" % plane.throttle,
                self.size[0]*3/128, self.size[1]*13/48,
                color_id='white', mode='topleft')
        self.draw_text("ALTITUDE",
                self.size[0]*3/128, self.size[1]*17/48,
                color_id='white', mode='topleft')
        self.draw_text("%i FT" % (plane.altitude),
                self.size[0]*3/128, self.size[1]*3/8,
                color_id='white', mode='topleft')
        self.draw_text("DAMAGE",
                self.size[0]*3/128, self.size[1]*11/24,
                color_id='white', mode='topleft')
        self.draw_text("%.1f%%" % (100 - plane.health),
                self.size[0]*3/128, self.size[1]*23/48,
                color_id='white', mode='topleft')
        self.draw_text("SPEED",
                self.size[0]*5/16, self.size[1]/4,
                color_id='white', mode='topleft')
        self.draw_text("%.1f KTS" % (plane.speed / 0.6),
                self.size[0]*5/16, self.size[1]*13/48,
                color_id='white', mode='topleft')
        self.draw_text("STL ALT LOSS",
                self.size[0]*5/16, self.size[1]*17/48,
                color_id='white', mode='topleft')
        self.draw_text("%.1f FT/S" % (-plane.gravity),
                self.size[0]*5/16, self.size[1]*3/8,
                color_id='white', mode='topleft')
        self.draw_text("VERT SPD",
                self.size[0]*5/16, self.size[1]*11/24,
                color_id='white', mode='topleft')
        self.draw_text("%.1f FT/S" % (plane.vertical_velocity),
                self.size[0]*5/16, self.size[1]*23/48,
                color_id='white', mode='topleft')
        

        # throttle bar
        pygame.draw.rect(self.screen, self.colors['red'],
                (self.size[0]*15/128, self.size[1]*71/192,
                self.size[0]/64, self.size[1]*25/192))
        pygame.draw.rect(self.screen, self.colors['white'],
                (self.size[0]*15/128, self.size[1]*19/48,
                self.size[0]/64, self.size[1]*5/48))
        pygame.draw.rect(self.screen, self.colors['green'],
                (self.size[0]*15/128,
                float(self.size[1])/self.DEFAULT_SIZE[1]*(480-plane.throttle),
                self.size[0]/64,
                float(self.size[1])/self.DEFAULT_SIZE[1]*plane.throttle))

        # status
        for line_id in range(len(self.status)):
            self.draw_text(self.status[line_id],
                    self.size[0]*5/256, self.size[1]*(21/32.0+1.0/24*line_id),
                    font_id="large", color_id='white', mode='topleft')

        # warnings
        if self.warnings["pullup"]:
            self.screen.blit(self.images['msg_pullup'],
                    (self.size[0]*5/32, self.size[1]*49/96))
        elif self.warnings["terrain"]:
            self.screen.blit(self.images['msg_warning'],
                    (self.size[0]*187/1280, self.size[1]*7/40))
        elif self.warnings["stall"]:
            self.screen.blit(self.images['msg_stall'],
                    (self.size[0]*33/1280, self.size[1]*491/960))
        elif self.warnings["dontsink"]:
            self.screen.blit(self.images['msg_dontsink'],
                    (self.size[0]*19/80, self.size[1]*109/192))
        elif self.warnings["bankangle"]:
            self.screen.blit(self.images['msg_bankangle'],
                    (self.size[0]/40, self.size[1]*109/192))
        elif self.warnings["overspeed"]:
            self.screen.blit(self.images['msg_overspeed'],
                    (self.size[0]*73/256, self.size[1]*49/96))
        if not plane.ap_enabled:
            self.screen.blit(self.images['msg_apdisconnect'],
                    (self.size[0]*7/64, self.size[1]*11/96))
            self.status = ["Autopilot disengaged"]
        else:
            self.screen.blit(self.images['msg_apengaged'],
                    (self.size[0]*17/128, self.size[1]*11/96))
            self.status = ["Autopilot engaged..."]

    def control_plane(self):
        """Allows you to control the plane."""
        for plane in self.planes:
            if plane.id == 0: break
        if not plane.ap_enabled:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                plane.roll_level -= (1.0 / self.fps)
                if plane.roll_level < -4: plane.roll_level = -4
            elif keys[pygame.K_RIGHT]:
                plane.roll_level += (1.0 / self.fps)
                if plane.roll_level > 4: plane.roll_level = 4
            if keys[pygame.K_UP]:
                plane.vertical_roll_level -= (1.0 / self.fps)
                if plane.vertical_roll_level < -4:
                    plane.vertical_roll_level = -4
            elif keys[pygame.K_DOWN]:
                plane.vertical_roll_level += (1.0 / self.fps)
                if plane.vertical_roll_level > 4:
                    plane.vertical_roll_level = 4
            if keys[pygame.K_F2]:
                plane.throttle -= (8.0 / self.fps)
                if plane.throttle < 0: plane.throttle = 0
            elif keys[pygame.K_F3]:
                plane.throttle += (8.0 / self.fps)
                if plane.throttle > 130: plane.throttle = 130

            for event in self.events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1: plane.throttle = 0
                    elif event.key == pygame.K_F4: plane.throttle = 100
                    elif event.key == pygame.K_z: plane.ap_enabled = True

    def run_warnings(self):
        """Runs warnings."""
        if self.warnings["pullup"]:
            self.sounds['pullup'].play()
            self.warnings["pullup"] = False
        elif self.warnings["terrain"]:
            self.sounds['terrain'].play()
            self.warnings["terrain"] = False
        elif self.warnings["stall"]:
            self.sounds['stall'].play()
            self.warnings["stall"] = False
        elif self.warnings["dontsink"]:
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

    def log(self):
        """Writes in the log.

        The log logs every 5 seconds.  It records:
         - The game tick that the log is recording at
         - How many milliseconds long that tick was
         - The coordinates, heading and score of all planes
         - The coordinates of all objectives
        """
        self.log_file = open(self.log_filepath, 'at')
        output = []
        output.append("%i\t%i\t" % (self.tick,
                (self.time-self.previous_time) * 1000))
        for plane_id in range(len(self.planes)):
            for plane in self.planes:
                if plane.id == plane_id: break
            output.append(
                    "%i\t%i\t%i\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\
\t%.2f\t%.2f\t%.2f\t%i\t%.1f\t"
                    % (plane.upos[0], plane.upos[1], plane.altitude,
                    plane.speed, plane.acceleration,
                    plane.vertical_velocity, plane.throttle,
                    plane.heading, plane.pitch, plane.roll_level,
                    plane.roll, plane.vertical_roll_level, plane.points,
                    100 - plane.health))
        for objective_id in range(len(self.objectives)):
            for objective in self.objectives:
                if objective.id == objective_id: break
            output.append("%.i\t%i\t%i\t" % (objective.upos[0],
                    objective.upos[1], objective.altitude))
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
        for plane in self.planes:
            if plane.id == 0: break
        self.control_plane()
        self.airspace.update(self)
        self.draw()
        if plane.exit_code != 0:
            self.log_file = open(self.log_filepath, 'at')
            self.log_file.write("[!] Exited main loop with exitcode %i"
                    % plane.exit_code)
            self.log_file.close()
            if self.output_log: print("[!] Exited main loop with exitcode %i"
                    % plane.exit_code)
            self.exit_title = self.EXIT_TITLES[plane.exit_code]
            self.exit_reason = self.EXIT_REASONS[plane.exit_code]
            if plane.exit_code not in [0, 7]:
                self.exit_reason %= plane.points
            self.exit_code = plane.exit_code
            self.stage = 2
        pygame.display.flip()
        for event in self.events:
            if event.type == pygame.QUIT:
                plane.exit_code = 2
                self.events.remove(event)
            elif event.type == self.event_log:
                self.log()
            elif event.type == self.event_warn:
                self.run_warnings()
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
##        except Exception as e:
##            print(e)
##            raise ValueError("%s is not a stage." % new_value)
        self._stage = new_value
