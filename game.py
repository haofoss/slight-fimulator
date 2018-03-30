#!/usr/bin/env python

"""The game code.

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

import argparse
import datetime
import io
import json
import logging
import math
import os
import sys
import time
import zipfile

import pygame

from __init__ import __version__

class Client(pygame.rect.Rect):
    """The client.  Handles drawing and logging."""
    GAME_STAGES = {} # The methods used to enter each stage
    GAME_LOOPS = {} # The loops for each stage
    PATH = os.path.dirname(os.path.realpath(__file__))
    LOG_PATH = os.path.join(PATH, "logs")
    DEFAULT_SIZE = (1280, 960)
    DEFAULT_ASPECT_RATIO = DEFAULT_SIZE[0] / DEFAULT_SIZE[1]
    NEXT_ID = 0 # The next unused ID for this class
    EXIT_TITLES = (
        "UNEXPECTED",
        "Congratulations",
        "Closed",
        "Failed",
        "Failed",
        "Failed",
        "Failed",
        "UNEXPECTED"
    )
    EXIT_REASONS = (
        "Exited with exitcode 0 (unexpected). Please report.",
        "You have completed the objective with a score of {}.",
        "The game has been closed. Your score was {}.",
        "You crashed your aircraft. Your score was {}.",
        "Left the operation area. Your score was {}.",
        "The aircraft was overstressed. Your score was {}.",
        "The aircraft exceeded its service ceiling altitude.  \
Your score was {}.",
        "Exited with exitcode 7 (unexpected). Please report."
    )
    DEFAULT_OPTIONS = {
        'music': True,
        'sound': True,
        'units': 0,
        'controls': { # -1 means no key
            'horiz-': pygame.K_LEFT,
            'horiz+': pygame.K_RIGHT,
            'vert-': pygame.K_UP,
            'vert+': pygame.K_DOWN,
            'throttle+': pygame.K_F4,
            'throttle-': pygame.K_F2,
            'throttle-0': pygame.K_F1,
            'throttle-25': pygame.K_F3,
            'throttle-50': -1,
            'throttle-75': pygame.K_F5,
            'throttle-100': -1,
            'autopilot': pygame.K_z,
            'pause': pygame.K_PAUSE,
            'quit': pygame.K_ESCAPE
        }
    }
    CONTROLS = [
        'horiz-', 'horiz+', 'vert-', 'vert+',
        'throttle+', 'throttle-', 'throttle-0', 'throttle-25',
        'throttle-50', 'throttle-75', 'throttle-100',
        'autopilot', 'pause', 'quit',
    ]
    DEFAULT_CONTROLS = DEFAULT_OPTIONS['controls']
    CONTROL_NAMES = {
        'horiz-': "Left",
        'horiz+': "Right",
        'vert-': "Up",
        'vert+': "Down",
        'throttle+': "Increase Throttle",
        'throttle-': "Decrease Throttle",
        'throttle-0': "Set Throttle to 0%",
        'throttle-25': "Set Throttle to 25%",
        'throttle-50': "Set Throttle to 50%",
        'throttle-75': "Set Throttle to 75%",
        'throttle-100': "Set Throttle to 100%",
        'autopilot': "Autopilot",
        'pause': "Pause",
        'quit': "Quit",
    }
    UNITS = ( # The unit sets
        {
            'name': "SI", # Set name
            'speed': { # Unit
                'name': "M/S", # Unit name
                'value': 1, # Value in SI base units
                'round-to': 1 # Decimal places to use
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

    def __init__(self, window_size=DEFAULT_SIZE, player_id=None):
        """Initializes the instance. Does not start the game."""
        super(Client, self).__init__(0, 0, *window_size)
        # Finds a folder if possible, otherwise tries a zip archive
        if "resources" in os.listdir(self.PATH):
            self.resources_path = os.path.join(self.PATH, "resources")
        elif "resources.zip" in os.listdir(self.PATH):
            self.resources_path = os.path.join(self.PATH, "resources.zip")
        else: raise Exception("Resources not found!")
        self.clock = pygame.time.Clock() # Controls ticking
        self.max_fps = 60 # Controls max fps
        # Gets a player ID
        if player_id is None:
            self._id = Client.NEXT_ID
            Client.NEXT_ID += 1
        else: self._id = player_id
        # Parses command line arguments
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            '-v', '--version', action='store_true',
            help='display the version and exit')
        self.parser.add_argument(
            '--log-to-file', action='store_true',
            help='log to a file instead of stdout')
        self.parser.add_argument(
            '--log-level', default='WARNING',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='the least important log item type to display')
        self.args = self.parser.parse_args()
        # Handles command line arguments
        if self.args.version:
            print("Slight Fimulator v{}".format(__version__))
            sys.exit()
        self.log_to_file = self.args.log_to_file
        self.log_level = getattr(logging, self.args.log_level)
        # Gets controls
        if os.path.exists("{}/.options.json".format(self.PATH)):
            # options file found - use these
            with open("{}/.options.json".format(self.PATH), 'rt') as f:
                prefs = json.load(f)
                self.controls = prefs['controls']
                self.music_enabled = prefs['music']
                self.sound_enabled = prefs['sound']
                self.unit_id = prefs['units']
        else:
            self.controls = self.DEFAULT_CONTROLS.copy()
            self.music_enabled = Client.DEFAULT_OPTIONS['music']
            self.sound_enabled = Client.DEFAULT_OPTIONS['sound']
            self.unit_id = Client.DEFAULT_OPTIONS['units']
    @property
    def id_(self):
        """Get the ID."""
        return self._id
    @property
    def stage(self):
        """Get the stage."""
        return self._stage
    @stage.setter
    def stage(self, new_value):
        """Set the stage variable to change the stage."""
        self.GAME_STAGES[new_value](self)
        self._stage = new_value
    @property
    def exit_code(self):
        """Return the exit code."""
        if self.plane.health <= 0:
            return 5 # Overstressed the aircraft
        elif (self.plane.points >= self.airspace.POINTS_REQUIRED
              and self.plane.altitude <= 0):
            return 1 # You Won!
        # position-related exit
        if self.plane.altitude > self.airspace.MAX_ALTITUDE:
            return 6
        elif (self.plane.altitude <= 0
              and self.plane.total_vertical_velocity < -20):
            return 3
        elif not self.airspace.in_bounds(self.plane, False):
            return 4

    def mainloop(self, airspace):
        """The game's loop."""
        # Setup Pygame
        pygame.init()
        self.screen = pygame.display.set_mode(self.size, pygame.RESIZABLE)
        pygame.display.set_caption(
            "Slight Fimulator v{}".format(__version__))
        # Setup resources
        self.load_resources()
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()
        if not self.music_enabled:
            pygame.mixer.music.set_volume(0)
        self.scale_images()
        # Setup airspace
        self.airspace = airspace
        self.airspace_rect = pygame.rect.Rect(
            self.size[0]*7/16, self.size[1]/24,
            self.size[0]*35/64, self.size[1]*35/48)
        # Setup plane and objective
        self.plane = self.airspace.add_plane(player_id=self.id_)
        self.airspace.generate_objective()
        for obj in self.airspace.objectives: # Get closest objective
            self.closest_objective = obj
        # Makes a list of length [# of keys registered by Pygame + 1]
        # The +1 is so key # -1 registers nothing
        self.keys_held = [0] * (len(pygame.key.get_pressed()) + 1)
        self.music_playing = None
        self.stage = 0 # The stage (Beginning, In-Game, End)
        self.paused = 0 # 0 if unpaused; non-0 otherwise
        self.status = "Fly to the objective."
        self.warnings = {
            "terrain": {
                "condition": False,
                "show": True
            },
            "pullup": {
                "condition": False,
                "show": True
            },
            "overspeed": {
                "condition": False,
                "show": True
            },
            "stall": {
                "condition": False,
                "show": True
            },
            "bank_angle": {
                "condition": False,
                "show": True
            },
            "altitude": {
                "condition": False,
                "show": True
            },
            "autopilot": {
                "condition": True,
                "show": False
            }
        }
        # Time variables
        self.startup_time = time.time()
        self.previous_time = time.time()
        self.time = time.time()
        self.tick = 0
        # Custom timer events
        self.event_log = pygame.USEREVENT
        pygame.time.set_timer(self.event_log, 5000)
        self.event_warn = pygame.USEREVENT + 1
        pygame.time.set_timer(self.event_warn, 2000)
        self.event_toggletext = pygame.USEREVENT + 2
        pygame.time.set_timer(self.event_toggletext, 333)

        # Game loop
        self.done = False
        while not self.done:
            self.clock.tick(self.max_fps) # Handles FPS
            self.fps = self.clock.get_fps() # Stores FPS in a variable
            self.events = pygame.event.get() # Gets events
            self.screen.fill(self.colors['background'])
            self.GAME_LOOPS[self.stage](self) # Runs the correct loop
            for event in self.events:
                if event.type == pygame.QUIT or self.stage == 'END':
                    self.done = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == self.controls['quit']:
                        self.done = True
                elif event.type == pygame.VIDEORESIZE:
                    self.update_screen_size(event.size)
        # This runs when the program is finished running
        pygame.quit() # Exits Pygame
        if self.resources_path.endswith('.zip'): # Close Zip
            self.resources.close()
        # Save preferences
        preferences = {
            'music': self.music_enabled,
            'sound': self.sound_enabled,
            'units': self.unit_id,
            'controls': self.controls
        }
        with open('{}/.options.json'.format(self.PATH), 'wt') as f:
            json.dump(preferences, f)

    def reset(self):
        """Resets the game for another play."""
        self.airspace.remove_plane(self.id_)
        for obj in self.airspace.objectives:
            self.airspace.objectives.remove(obj)
        self.plane = self.airspace.add_plane(player_id=self.id_)
        self.airspace.generate_objective()
        for obj in self.airspace.objectives: # Get closest objective
            self.closest_objective = obj

    def prepare_log(self):
        """Prepare the log."""
        if not self.log_to_file: # Settings for output logging
            logging.basicConfig(
                datefmt="%H:%M:%S", format=
                "%(asctime)s    %(levelname)s\t%(message)s",
                level=self.log_level)
        else: # Settings for file logging
            warn = False
            if not os.path.isdir(self.LOG_PATH):
                # If no logging directory, create one
                os.makedirs(self.LOG_PATH)
                warn = True
            logging.basicConfig(
                datefmt="%H:%M:%S", level=self.log_level,
                format="%(asctime)s    %(levelname)s\t%(message)s",
                filename=os.path.join(
                    self.LOG_PATH, "{}.log".format(
                        datetime.datetime.now().strftime(
                            "%Y-%m-%d-%H-%M-%S"))))
            if warn: # If a logging directory was created, warn the user
                logging.warning(
                    "No logging directory found, created directory %s",
                    os.path.abspath(self.LOG_PATH))

        # If on debug mode, log headings
        output = []
        # first row labels
        output.append("TIME\t")
        for plane_id in range(len(self.airspace.planes)):
            output.append("PLN-%i\t\t\t\t\t\t\t\t\t\t\t\t" % plane_id)
        for objective_id in range(len(self.airspace.objectives)):
            output.append("OBJ-%i\t\t\t" % objective_id)
        logging.debug(''.join(output))
        output = []
        # second row labels - tick 0 stats
        output.append("TICK:\t")
        for plane_id in range(len(self.airspace.planes)):
            for plane in self.airspace.planes:
                if plane.id_ == plane_id:
                    output.append(plane.LABELS)
                    break
        for objective_id in range(len(self.airspace.objectives)):
            for objective in self.airspace.objectives:
                if objective.id_ == objective_id:
                    output.append(objective.LABELS)
                    break
        logging.debug(''.join(output)) # Log it!

    def load_resources(self):
        """Load the game's resources. Compatible with zips.

        Images, Sounds, Colors and Fonts use Pygame Objects.
        Music uses filepaths/file objects (both compatible with
        pygame.mixer.music.load)

        Directory Layout:

        Root folder or zip archive
         -> Images
             -> insert all image files, any pygame-compatible extension
         -> Sounds
             -> insert all sound files, any pygame-compatible extension
         -> Music
             -> insert all music files, will not load as Sound objects
         -> colors.txt OR colours.txt (lines look like: colorid=hexcode)
         -> fonts.txt (lines look like: fontid=fontname size)

        If font size is a decimal, multiplies font size by the window's height
         (this includes numbers ending in .0)
        Any line in fonts.txt or colors.txt that starts with a # is ignored
        Blank lines are also ignored
        """
        # Create dictionnaries to put the resources in
        self.images = {}
        self.sounds = {}
        self.music_files = {}
        self.colors = {}
        self.fonts = {}
        self.font_data = {}
        if self.resources_path.endswith('.zip'): # Zip Archive
            self.resources = zipfile.ZipFile(self.resources_path)
            for filename in self.resources.namelist():
                if filename.endswith('/'):
                    pass # Is a folder, don't extract
                elif filename.startswith('Images/'): # Load Images
                    image_data = self.resources.read(filename)
                    image_bytes_io = io.BytesIO(image_data)
                    image = pygame.image.load(image_bytes_io)
                    image_name = \
                            filename.lower()[7:].split('.')[0]
                    self.images[image_name] = image
                elif filename.startswith('Sounds/'): # Load Sounds
                    sound_data = self.resources.read(filename)
                    sound_bytes_io = io.BytesIO(sound_data)
                    sound = pygame.mixer.Sound(sound_bytes_io)
                    sound_name = \
                            filename.lower()[7:].split('.')[0]
                    self.sounds[sound_name] = sound
                elif filename.startswith('Music/'): # Load Music
                    music_data = self.resources.read(filename)
                    music_bytes_io = io.BytesIO(music_data)
                    music_name = \
                            filename.lower()[6:].split('.')[0]
                    self.music_files[music_name] = music_bytes_io
                # Load Colours
                elif filename in ['colors.txt', 'colours.txt']:
                    colors_file = self.resources.open(filename)
                    for line in colors_file.readlines():
                        line = str(line.decode('utf-8'))
                        if line.strip() == '':
                            continue
                        elif line.strip()[0] == '#':
                            continue
                        colorname, color = line.split('=')
                        colorname = colorname.strip()
                        color = pygame.color.Color(color.strip())
                        self.colors[colorname] = color
                # Load Fonts
                elif filename == 'fonts.txt':
                    fonts_file = self.resources.open(filename)
                    for line in fonts_file.readlines():
                        line = str(line.decode('utf-8'))
                        if line.strip() == '':
                            continue
                        elif line.strip()[0] == '#':
                            continue
                        fontname, font = line.split('=')
                        fontname = fontname.strip()
                        font_info = font.strip().split(' ')
                        font = ' '.join(font_info[:-1])
                        size = int(float(font_info[-1]) * self.height)
                        if font.lower() in ['none', 'default']:
                            font = None
                        self.font_data[fontname] = font, float(
                            font_info[-1])
                        self.fonts[fontname] = pygame.font.Font(
                            font, size)
        else: # Directory
            images_path = os.path.join(self.resources_path, "Images")
            for image_name in os.listdir(images_path): # Load Images
                image_file = os.path.join(images_path, image_name)
                image_name = image_name.split('.')[0]
                image = pygame.image.load(image_file)
                self.images[image_name] = image
            sounds_path = os.path.join(self.resources_path, "Sounds")
            for sound_name in os.listdir(sounds_path): # Load Sounds
                sound_file = os.path.join(sounds_path, sound_name)
                sound_name = sound_name.split('.')[0]
                sound = pygame.mixer.Sound(sound_file)
                self.sounds[sound_name] = sound
            music_path = os.path.join(self.resources_path, "Music")
            for music_name in os.listdir(music_path): # Load Music
                music_file = os.path.join(music_path, music_name)
                music_name = music_name.split('.')[0]
                self.music_files[music_name] = music_file
            if "colors.txt" in os.listdir(self.resources_path):
                colors_file = open(os.path.join(
                    self.resources_path, "colors.txt"), 'rt')
            elif "colours.txt" in os.listdir(self.resources_path):
                colors_file = open(os.path.join(
                    self.resources_path, "colours.txt"), 'rt')
            else: colors_file = None
            if colors_file != None: # Load Colours
                for line in colors_file.readlines():
                    if line.strip() == '':
                        continue
                    elif line.strip()[0] == '#':
                        continue
                    colorname, color = line.split('=')
                    colorname = colorname.strip()
                    color = pygame.color.Color(color.strip())
                    self.colors[colorname] = color
                colors_file.close()
            try: # Load Fonts
                fonts_file = open(os.path.join(
                    self.resources_path, "fonts.txt"))
                for line in fonts_file.readlines():
                    if line.strip() == '':
                        continue
                    elif line.strip()[0] == '#':
                        continue
                    fontname, font = line.split('=')
                    fontname = fontname.strip()
                    font_info = font.strip().split(' ')
                    font = ' '.join(font_info[:-1])
                    size = int(float(font_info[-1]) * self.height)
                    if font.lower() in ['none', 'default']:
                        font = None
                    self.font_data[fontname] = font, float(font_info[-1])
                    self.fonts[fontname] = pygame.font.Font(font, size)
                fonts_file.close()
            except Exception as e:
                logging.warning(str(e))

    def draw_text(self, text, x, y=None, mode="center",
                  color_id=(0, 0, 0), font_id='default', antialias=1,
                  bg_color=None):
        """Draw text \"text\" at x, y."""
        if y is None:
            x, y = x # Handles iterable arguments
        # Gets the colour
        if color_id in self.colors.keys():
            color = self.colors[color_id]
        else:
            color = color_id
        if isinstance(color, str):
            color = pygame.color.Color(color)
        elif isinstance(color, (list, tuple)):
            if len(color) == 3:
                r, g, b = color
                color = pygame.color.Color(r, g, b)
            elif len(color) == 4:
                r, g, b, a = color
                color = pygame.color.Color(r, g, b, a)
        # Gets the background colour
        if isinstance(bg_color, str):
            bg_color = pygame.color.Color(bg_color)
        elif isinstance(bg_color, (list, tuple)):
            if len(bg_color) == 3:
                r, g, b = bg_color
                bg_color = pygame.color.Color(r, g, b)
            elif len(bg_color) == 4:
                r, g, b, a = bg_color
                bg_color = pygame.color.Color(r, g, b, a)
        # Gets the font
        if font_id in self.fonts.keys():
            font = self.fonts[font_id]
        else: # no font found
            try:
                font_info = font_id.strip().split(' ')
                font_name = ' '.join(font_info[:-1])
                size = font_info[-1]
                if '.' in size:
                    size = float(size) * self.size[1]
                else:
                    size = int(size)
                if font.lower() in ['none', 'default']:
                    font_name = None
                font = pygame.font.Font(font_name, size)
            except:
                raise ValueError("Invalid font %s" % font_id)
        # Calculate the text position
        text_obj = font.render(text, antialias, color)
        text_rect = text_obj.get_rect()
        setattr(text_rect, mode, (x, y))
        # Draw the text
        if bg_color:
            pygame.draw.rect(self.screen, bg_color, text_rect)
        self.screen.blit(text_obj, text_rect)

    def update_screen_size(self, new_size):
        """Update the screen size."""
        self.prev_size = self.size
        new_size = list(new_size)
        center = (new_size[0]/2, new_size[1]/2)
        # Keeps the aspect ratio the same
        if new_size[0] / new_size[1] > self.DEFAULT_ASPECT_RATIO:
            new_size[0] = new_size[1] * self.DEFAULT_ASPECT_RATIO
        elif new_size[0] / new_size[1] < self.DEFAULT_ASPECT_RATIO:
            new_size[1] = new_size[0] / self.DEFAULT_ASPECT_RATIO
        # Updates stuff
        self.size = new_size
        self.center = center
        self.airspace_rect.topleft = (
            self.x + self.width*7/16,
            self.y + self.height/24)
        self.airspace_rect.size = (self.width*35/64, self.height*35/48)
        self.scale_images()
        self.scale_fonts()

    def scale_images(self):
        """Set up the images with the correct size."""
        self.scaled_images = {}
        for image_name in self.images:
            x, y = self.images[image_name].get_rect().size
            x *= (self.width / self.DEFAULT_SIZE[0])
            y *= (self.height / self.DEFAULT_SIZE[1])
            x = int(x)
            y = int(y)
            self.scaled_images[image_name] = pygame.transform.scale(
                self.images[image_name], (x, y))

    def scale_fonts(self):
        """Set up the fonts with the correct size.

        Scales according to height."""
        self.font_names = self.fonts.keys()
        self.fonts = {}
        for font_name in self.font_names:
            self.fonts[font_name] = pygame.font.Font(
                self.font_data[font_name][0],
                int(self.font_data[font_name][1] * self.height))

    def draw(self):
        """Draw the info box and airspace."""
        # get closest objective
        closest_dist = float('inf')
        for obj in self.airspace.objectives:
            dist = ((self.plane.rect.x - obj.rect.x) ** 2
                    + (self.plane.rect.y - obj.rect.y) ** 2) ** 0.5
            if dist < closest_dist:
                closest_dist = dist
                closest_objective = obj
        self.closest_objective = closest_objective

        # attitude tape
        attitude_tape = pygame.transform.rotate(
            self.scaled_images['attitudetape-bg'],
            self.plane.roll_degrees)
        # calculate the position
        attitude_tape_rect = attitude_tape.get_rect()
        attitude_tape_rect.center = (
            self.x + self.width*55/256,
            self.y + self.height*9/24)
        offset_total = (
            attitude_tape_rect.height * 3/1600 * self.height
            / attitude_tape_rect.height * self.plane.pitch_degrees)
        offset_x = math.sin(self.plane.roll) * offset_total
        offset_y = math.cos(self.plane.roll) * offset_total
        attitude_tape_rect.x += offset_x
        attitude_tape_rect.y += offset_y

        attitude_tape_overlay = pygame.transform.rotate(
            self.scaled_images['attitudetape-overlay'],
            self.plane.roll_degrees)
        attitude_tape_overlay_rect = attitude_tape_overlay.get_rect()
        attitude_tape_overlay_rect.center = (
            self.x + self.width*55/256,
            self.y + self.height*9/24)
        offset_total = (
            attitude_tape_overlay_rect.height * 3/1600 * self.height
            / attitude_tape_overlay_rect.height
            * self.plane.pitch_degrees)
        offset_x = math.sin(self.plane.roll) * offset_total
        offset_y = math.cos(self.plane.roll) * offset_total
        attitude_tape_overlay_rect.x += offset_x
        attitude_tape_overlay_rect.y += offset_y
        self.screen.blit(attitude_tape, attitude_tape_rect)
        self.screen.blit(attitude_tape_overlay, attitude_tape_overlay_rect)
        # surrounding panels
        pygame.draw.rect(
            self.screen, self.colors['panel'],
            (self.x + self.size[0]*5/256, self.y + self.size[1]*5/48,
             self.size[0]*25/64, self.size[1]*7/48))
        pygame.draw.rect(
            self.screen, self.colors['panel'],
            (self.x + self.size[0]*5/256, self.y + self.size[1]*5/48,
             self.size[0]*15/128, self.size[1]*25/48))
        pygame.draw.rect(
            self.screen, self.colors['panel'],
            (self.x + self.size[0]*75/256, self.y + self.size[1]*5/48,
             self.size[0]*15/128, self.size[1]*25/48))
        pygame.draw.rect(
            self.screen, self.colors['panel'],
            (self.x + self.size[0]*5/256, self.y + self.size[1]/2,
             self.size[0]*25/64, self.size[1]*7/48))
        self.screen.blit(
            self.scaled_images['attitudecrosshair'],
            (self.x + self.size[0]*35/256, self.y + self.size[1]*9/24))

        # redraw background
        pygame.draw.rect(
            self.screen, self.colors['background'],
            (0, 0, self.x*2 + self.size[0], self.y + self.size[1]*5/48))
        pygame.draw.rect(
            self.screen, self.colors['background'],
            (0, 0, self.x + self.size[0]*5/256, self.y*2 + self.size[1]))
        pygame.draw.rect(
            self.screen, self.colors['background'],
            (0, self.y + self.size[1]*15/24,
             self.x*2 + self.size[0], self.y + self.size[1]*9/24))
        pygame.draw.rect(
            self.screen, self.colors['background'],
            (self.x + self.size[0]*105/256 - 1, 0,
             self.x + self.size[0]*151/256, self.y*2 + self.size[1]))
        # The -1 deals with an issue with sizing innacuracy.

        # draw NAV/airspace
        self.airspace.draw(self)

        # NAV text
        self.draw_text(
            "PLANE LOCATION",
            self.x + self.size[0]*29/64, self.y + self.size[1]/16,
            color_id='white', mode='topleft')
        self.draw_text(
            self.get_unit_text(self.plane.x, 'pos', 'X', False),
            self.x + self.size[0]*29/64, self.y + self.size[1]/12,
            color_id='white', mode='topleft')
        self.draw_text(
            self.get_unit_text(self.plane.z, 'pos', 'Z', False),
            self.x + self.size[0]*29/64, self.y + self.size[1]*5/48,
            color_id='white', mode='topleft')
        self.draw_text(
            self.get_unit_text(self.plane.altitude, 'pos', 'ALT'),
            self.x + self.size[0]*29/64, self.y + self.size[1]/8,
            color_id='white', mode='topleft')
        self.draw_text(
            "HEADING: %.1f\xb0" % self.plane.heading_degrees,
            self.x + self.size[0]*91/128, self.y + self.size[1]/16,
            color_id='white', mode='midtop')
        self.draw_text(
            "PITCH: %.1f\xb0" % self.plane.pitch_degrees,
            self.x + self.size[0]*91/128, self.y + self.size[1]/12,
            color_id='white', mode='midtop')
        self.draw_text(
            "SCORE: %i" % self.plane.points,
            self.x + self.size[0]*91/128, self.y + self.size[1]*5/48,
            color_id='white', mode='midtop')
        self.draw_text(
            "OBJECTIVE LOCATION",
            self.x + self.size[0]*31/32, self.y + self.size[1]/16,
            color_id='white', mode='topright')
        self.draw_text(
            self.get_unit_text(closest_objective.x, 'pos', 'X', False),
            self.x + self.size[0]*31/32, self.y + self.size[1]/12,
            color_id='white', mode='topright')
        self.draw_text(
            self.get_unit_text(closest_objective.z, 'pos', 'Z', False),
            self.x + self.size[0]*31/32, self.y + self.size[1]*5/48,
            color_id='white', mode='topright')
        self.draw_text(
            self.get_unit_text(closest_objective.altitude, 'pos', 'ALT'),
            self.x + self.size[0]*31/32, self.y + self.size[1]/8,
            color_id='white', mode='topright')

        # panel text
        self.draw_text(
            "THROTTLE",
            self.x + self.size[0]*3/128, self.y + self.size[1]/4,
            color_id='white', mode='topleft')
        self.draw_text(
            "%.1f%%" % self.plane.throttle,
            self.x + self.size[0]*3/128, self.y + self.size[1]*13/48,
            color_id='white', mode='topleft')
        self.draw_text(
            "GRAVITY",
            self.x + self.size[0]*3/128, self.y + self.size[1]*17/48,
            color_id='white', mode='topleft')
        self.draw_text(
            self.get_unit_text(-self.plane.gravity, 'speed'),
            self.x + self.size[0]*3/128, self.y + self.size[1]*3/8,
            color_id='white', mode='topleft')
        self.draw_text(
            "DAMAGE",
            self.x + self.size[0]*3/128, self.y + self.size[1]*11/24,
            color_id='white', mode='topleft')
        self.draw_text(
            "%.1f%%" % (100 - self.plane.health),
            self.x + self.size[0]*3/128, self.y + self.size[1]*23/48,
            color_id='white', mode='topleft')
        self.draw_text(
            "SPEED",
            self.x + self.size[0]*5/16, self.y + self.size[1]/4,
            color_id='white', mode='topleft')
        self.draw_text(
            self.get_unit_text(self.plane.speed, 'speed'),
            self.x + self.size[0]*5/16, self.y + self.size[1]*13/48,
            color_id='white', mode='topleft')
        self.draw_text(
            "HORIZ SPD",
            self.x + self.size[0]*5/16, self.y + self.size[1]*17/48,
            color_id='white', mode='topleft')
        self.draw_text(
            self.get_unit_text(self.plane.horizontal_speed, 'speed'),
            self.x + self.size[0]*5/16, self.y + self.size[1]*3/8,
            color_id='white', mode='topleft')
        self.draw_text(
            "VERT SPD",
            self.x + self.size[0]*5/16, self.y + self.size[1]*11/24,
            color_id='white', mode='topleft')
        self.draw_text(
            self.get_unit_text(self.plane.vertical_velocity, 'speed'),
            self.x + self.size[0]*5/16, self.y + self.size[1]*23/48,
            color_id='white', mode='topleft')

        # throttle bar
        pygame.draw.rect(self.screen, self.colors['red'],
                         (self.x + self.size[0]*15/128,
                          self.y + self.size[1]*76/192,
                          self.size[0]/64, self.size[1]*5/192))
        pygame.draw.rect(self.screen, self.colors['white'],
                         (self.x + self.size[0]*15/128,
                          self.y + self.size[1]*81/192,
                          self.size[0]/64, self.size[1]*15/192))
        pygame.draw.rect(self.screen, self.colors['green'],
                         (self.x + self.size[0]*15/128, self.y
                          + self.size[1]/self.DEFAULT_SIZE[1]
                          * (480-self.plane.throttle),
                          self.size[0]/64,
                          self.size[1]/self.DEFAULT_SIZE[1]
                          *self.plane.throttle))

        # status
        for line_id in range(len(self.status.split('\n'))):
            self.draw_text(self.status.split('\n')[line_id],
                           self.x + self.size[0]*5/256,
                           self.y + self.size[1]*(21/32+1/24*line_id),
                           font_id="large", color_id='white',
                           mode='topleft')
        # warnings
        if self.show_warning("pullup"):
            self.screen.blit(self.scaled_images['msg_pullup'],
                             (self.x + self.size[0]*5/32,
                              self.y + self.size[1]*49/96))
        if self.show_warning("terrain"):
            self.screen.blit(self.scaled_images['msg_warning'],
                             (self.x + self.size[0]*187/1280,
                              self.y + self.size[1]*7/40))
        if self.show_warning("stall"):
            self.screen.blit(self.scaled_images['msg_stall'],
                             (self.x + self.size[0]*33/1280,
                              self.y + self.size[1]*491/960))
        if self.show_warning("bank_angle"):
            self.screen.blit(self.scaled_images['msg_bankangle'],
                             (self.x + self.size[0]/40,
                              self.y + self.size[1]*109/192))
        if self.show_warning("overspeed"):
            self.screen.blit(self.scaled_images['msg_overspeed'],
                             (self.x + self.size[0]*73/256,
                              self.y + self.size[1]*49/96))
        # autopilot message
        if self.plane.autopilot_enabled:
            self.screen.blit(self.scaled_images['msg_apengaged'],
                             (self.x + self.size[0]*17/128,
                              self.y + self.size[1]*11/96))
        else:
            self.screen.blit(self.scaled_images['msg_apdisconnect'],
                             (self.x + self.size[0]*7/64,
                              self.y + self.size[1]*11/96))
        if self.paused:
            # calculate the coordinates for the buttons
            self.btn_settings = pygame.rect.Rect(
                self.x + self.width*5/256, self.y + self.height*5/96,
                self.width / 6, self.height / 24)
            # draw the buttons
            pygame.draw.rect(self.screen, self.colors['panel'],
                             self.btn_settings)
            self.draw_text("Settings", self.btn_settings.center,
                           color_id='white')

    def get_unit_text(self, value, unit_name, label=None,
                      include_unit=True):
        """Get text in a certain unit."""
        if label is None:
            text = (
                "%%.%if" % self.UNITS[self.unit_id][unit_name][
                    'round-to']
                % (value * self.UNITS[self.unit_id][unit_name]['value']))
        else:
            text = ("%%s: %%.%if"
                    % self.UNITS[self.unit_id][unit_name]['round-to']
                    % (label, value
                       * self.UNITS[self.unit_id][unit_name]['value']))
        if include_unit: # add the unit name
            text = ' '.join((text, self.UNITS[self.unit_id][unit_name][
                'name']))
        return text

    def control_plane(self):
        """Control the plane."""
        if not self.plane.autopilot_enabled:
            keys = pygame.key.get_pressed()
            # Combine  keys and self.keys_held & remove  duplicates
            for keyid, key in enumerate(keys):
                if key:
                    self.keys_held[keyid] += 1
                else:
                    self.keys_held[keyid] = 0
            # left/right
            self.plane.roll_level -= ((self.keys_held[self.controls[
                'horiz-']] / 3) ** .75 / self.fps)
            self.plane.roll_level += ((self.keys_held[self.controls[
                'horiz+']] / 3) ** .75 / self.fps)
            # up/down
            self.plane.vertical_roll_level -= ((self.keys_held[
                self.controls['vert-']] / 3) ** .75 / self.fps)
            self.plane.vertical_roll_level += ((self.keys_held[
                self.controls['vert+']] / 3) ** .75 / self.fps)
            # throttle
            self.plane.throttle -= ((self.keys_held[self.controls[
                'throttle-']] / 3) ** .75 / self.fps)
            self.plane.throttle += ((self.keys_held[self.controls[
                'throttle+']] / 3) ** .75 / self.fps)
            # keypress events
            for event in self.events:
                if event.type == pygame.KEYDOWN:
                    if event.key == self.controls['throttle-0']:
                        self.plane.throttle = 0
                    elif event.key == self.controls['throttle-25']:
                        self.plane.throttle = 25
                    elif event.key == self.controls['throttle-50']:
                        self.plane.throttle = 50
                    elif event.key == self.controls['throttle-75']:
                        self.plane.throttle = 75
                    elif event.key == self.controls['throttle-100']:
                        self.plane.throttle = 100
                    elif event.key == self.controls['autopilot']:
                        self.plane.enable_autopilot()

    def calculate_warnings(self):
        """Determine what warnings to be turned on and off."""
        self.warnings["stall"]["condition"] = (
            self.plane.speed < self.plane.MAX_SPEED * 0.2
            and self.plane.altitude != 0)
        self.warnings["overspeed"]["condition"] = (
            self.plane.speed > self.plane.MAX_SPEED * 0.75)
        self.warnings["bank_angle"]["condition"] = (
            abs(self.plane.roll_degrees) >= 30)
        self.warnings["pullup"]["condition"] = (
            self.plane.altitude <= 1000
            and self.plane.total_vertical_velocity <= -20)
        self.warnings["terrain"]["condition"] = (
            self.plane.altitude <= 500
            and self.plane.speed > self.plane.MAX_SPEED * 0.3)
        self.warnings["altitude"]["condition"] = (
            abs(self.plane.altitude
                - self.closest_objective.altitude)
            <= self.airspace.ALTITUDE_WITHIN)
        if not self.warnings["altitude"]["condition"]:
            self.warnings["altitude"]["show"] = True
        self.warnings["autopilot"]["condition"] = (
            not self.plane.autopilot_enabled)
        if not self.warnings["autopilot"]["condition"]:
            self.warnings["autopilot"]["show"] = True

    def show_warning(self, warning_name):
        """Return whether a warning should be shown/played or not."""
        return (self.warnings[warning_name]["condition"]
                and self.warnings[warning_name]["show"])

    def play_sounds(self):
        """Play warning sounds."""
        if not self.sound_enabled:
            return
        if self.show_warning("pullup"):
            self.sounds['pullup'].play()
        elif self.show_warning("terrain"):
            self.sounds['terrain'].play()
        elif self.show_warning("stall"):
            self.sounds['stall'].play()
        if self.show_warning("bank_angle"):
            self.sounds['bankangle'].play()
        if self.show_warning("overspeed"):
            self.sounds['overspeed'].play()
        if self.show_warning("altitude"):
            self.sounds['altitude'].play()
            self.warnings['altitude']['show'] = False
        if self.show_warning("autopilot"):
            self.sounds['apdisconnect'].play()
            self.warnings['autopilot']['show'] = False

    def log(self):
        """Write in the log if in debug mode.

        The log logs every 5 seconds.  It records:
         - The game tick that the log is recording at
         - How many milliseconds long that tick was
         - The coordinates, heading and score of all planes
         - The coordinates of all objectives
        If the argument text is specified, logs that instead.
        """
        output = []
        output.append("%i\t" % self.tick)
        # outputs stats in the correct order
        for plane_id in range(len(self.airspace.planes)):
            for plane in self.airspace.planes:
                if plane.id_ == plane_id:
                    output.append(plane.__repr__(False))
                    break
        for objective_id in range(len(self.airspace.objectives)):
            for objective in self.airspace.objectives:
                if objective.id_ == objective_id:
                    output.append(objective.__repr__(False))
                    break
        logging.debug(''.join(output))

    def get_tick_values(self):
        """Prepare the values for the log."""
        self.tick += 1
        self.previous_time = self.time
        self.time = time.time()

    # -------------------------------------------------------------------
    # MAIN LOOPS
    # -------------------------------------------------------------------

    def startup_screen(self):
        """Activate the startup screen. Stage=0"""
        if self.music_playing != 'chilled-eks':
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.music_files['chilled-eks'])
            self.music_playing = 'chilled-eks'
            pygame.mixer.music.play(-1)
    def game_loop_startup(self):
        """One iteration of the startup screen loop."""
        # Draw the startup screen
        self.screen.blit(self.scaled_images['logo'],
                         ((self.x + self.width
                           - self.images['logo'].get_width()) / 2,
                          self.height/18.8))
        self.screen.blit(self.scaled_images['logotext'],
                         ((self.x + self.width
                           - self.images['logotext'].get_width()) / 2,
                          self.height/2.4))
        self.screen.blit(self.scaled_images['titleprompt'],
                         (self.x + self.width*35/64,
                          self.y + self.height*35/48))
        # calculate the coordinates for the buttons
        btn_play = pygame.rect.Rect(
            self.x + self.width*5/256, self.y + self.height*5/192,
            self.width / 6, self.height / 24)
        btn_help = pygame.rect.Rect(
            self.x + self.width*5/256, self.y + self.height*17/192,
            self.width / 6, self.height / 24)
        btn_settings = pygame.rect.Rect(
            self.x + self.width*5/256, self.y + self.height*29/192,
            self.width / 6, self.height / 24)
        # draw the buttons
        pygame.draw.rect(self.screen, self.colors['panel'], btn_play)
        self.draw_text("Play", btn_play.center, color_id='white')
        pygame.draw.rect(self.screen, self.colors['panel'], btn_help)
        self.draw_text("Instructions", btn_help.center, color_id='white')
        pygame.draw.rect(self.screen, self.colors['panel'], btn_settings)
        self.draw_text("Settings", btn_settings.center, color_id='white')
        pygame.display.flip()
        # Events
        for event in self.events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.stage = 1 # On pressing ENTER, start game
                elif event.key == pygame.K_ESCAPE:
                    self._stage = 'END'
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn_play.collidepoint(event.pos):
                    self.stage = 1 # On mouse click, start game
                elif btn_settings.collidepoint(event.pos):
                    self.stage = 'settings'
    GAME_STAGES[0] = startup_screen
    GAME_LOOPS[0] = game_loop_startup

    def settings_screen(self):
        """Activate the settings screen. Stage=settings"""
        self.prev_stage = self.stage
        self.control_selected = None
    def game_loop_settings(self):
        """The loop for the settings screen."""
        # back button
        btn_back = pygame.rect.Rect(
            self.x + self.width*5/256, self.y + self.height*5/192,
            self.width / 6, self.height / 24)
        pygame.draw.rect(self.screen, self.colors['panel'], btn_back)
        self.draw_text("Back", btn_back.center, color_id='white')
        # reset button
        btn_reset = pygame.rect.Rect(
            self.x + self.width*5/256, self.y + self.height*17/192,
            self.width / 6, self.height / 24)
        pygame.draw.rect(self.screen, self.colors['panel'], btn_reset)
        self.draw_text(
            "Reset Options", btn_reset.center, color_id='white')
        # music and sound
        btn_music = pygame.rect.Rect(
            self.x + self.width*5/256, self.y + self.height*33/192,
            self.width / 6, self.height / 24)
        pygame.draw.rect(self.screen, self.colors['panel'], btn_music)
        self.draw_text(
            "Music {}".format(
                "Enabled" if self.music_enabled else "Disabled"),
            btn_music.center, color_id='white')
        btn_sound = pygame.rect.Rect(
            self.x + self.width*5/256, self.y + self.height*45/192,
            self.width / 6, self.height / 24)
        pygame.draw.rect(self.screen, self.colors['panel'], btn_sound)
        self.draw_text(
            "Sound {}".format(
                "Enabled" if self.sound_enabled else "Disabled"),
            btn_sound.center, color_id='white')
        btn_units = pygame.rect.Rect(
            self.x + self.width*5/256, self.y + self.height*57/192,
            self.width / 6, self.height / 24)
        pygame.draw.rect(self.screen, self.colors['panel'], btn_units)
        self.draw_text(
            "Units: {}".format(Client.UNITS[self.unit_id]['name']),
            btn_units.center, color_id='white')
        # Control Buttons
        x = 65
        y = 5
        control_buttons = []
        for c in Client.CONTROLS:
            # Get key name
            k = self.controls[c]
            if self.control_selected == c:
                k = "Please press a key"
            elif k == -1:
                k = "No Key"
            else:
                k = pygame.key.name(k).title()
            # Create and draw button
            button = pygame.rect.Rect(
                self.x + self.width*x/256, self.y + self.height*y/192,
                self.width / 6, self.height / 24)
            pygame.draw.rect(self.screen, self.colors['panel'], button)
            self.draw_text(
                "{}: {}".format(Client.CONTROL_NAMES[c], k),
                button.center, color_id='white')
            control_buttons.append(button)
            # Calculate next button's position
            y += 12
            if y > 76:
                y = 5
                x += 50
        pygame.display.flip()
        for event in self.events:
            if event.type == pygame.MOUSEBUTTONUP:
                # Use the un-click instead of the click
                if btn_back.collidepoint(event.pos):
                    self.stage = self.prev_stage
                elif btn_reset.collidepoint(event.pos):
                    self.controls = self.DEFAULT_CONTROLS.copy()
                    self.music_enabled = Client.DEFAULT_OPTIONS['music']
                    if self.music_enabled:
                        pygame.mixer.music.set_volume(1)
                    else:
                        pygame.mixer.music.set_volume(0)
                    self.sound_enabled = Client.DEFAULT_OPTIONS['sound']
                    self.unit_id = Client.DEFAULT_OPTIONS['units']
                elif btn_music.collidepoint(event.pos):
                    if self.music_enabled:
                        self.music_enabled = False
                        # Set volume instead of stopping music
                        # This allows music to run as normal,
                        # just muted.
                        pygame.mixer.music.set_volume(0)
                    else:
                        self.music_enabled = True
                        pygame.mixer.music.set_volume(1)
                elif btn_sound.collidepoint(event.pos):
                    self.sound_enabled = not self.sound_enabled
                elif btn_units.collidepoint(event.pos):
                    self.unit_id += 1
                    if self.unit_id >= len(Client.UNITS):
                        self.unit_id = 0
                else:
                    for btn in control_buttons:
                        if btn.collidepoint(event.pos):
                            self.control_selected = Client.CONTROLS[
                                control_buttons.index(btn)]
            elif event.type == pygame.KEYDOWN:
                if self.control_selected:
                    self.controls[self.control_selected] = event.key
                    self.control_selected = None
    GAME_STAGES['settings'] = settings_screen
    GAME_LOOPS['settings'] = game_loop_settings

    def main_screen(self):
        """Activate the main game screen. Stage=1"""
        if self.music_playing != 'chip-respect':
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.music_files['chip-respect'])
            self.music_playing = 'chip-respect'
            pygame.mixer.music.play(-1)
        self.prepare_log()
        self.log()
        self.btn_settings = pygame.rect.Rect(
                self.x + self.width*5/256, self.y + self.height*5/96,
                self.width / 8, self.height / 36)
    def game_loop_main(self):
        """One iteration of the main loop."""
        if not self.paused:
            self.control_plane()
            self.airspace.update()
            self.calculate_warnings()
            self.draw()
        elif self.paused != 1:
            self.draw()
            self.draw_text("PAUSED", self.airspace_rect.center,
                           color_id='white', font_id='large')
        else:
            self.draw()
        if self.exit_code: # If finished,
            logging.info("Exited main loop with exitcode %i",
                         self.exit_code)
            self.exit_title = self.EXIT_TITLES[self.exit_code]
            self.exit_reason = self.EXIT_REASONS[self.exit_code]
            self.exit_reason = self.exit_reason.format(self.plane.points)
            self.stage = 2
        pygame.display.flip()
        for event in self.events:
            if event.type == pygame.QUIT:
                pass
            elif event.type == pygame.KEYDOWN:
                if event.key == self.controls['pause']:
                    if self.paused:
                        logging.info("Player unpaused")
                        self.plane._time += time.time() - self.pause_start
                        self.paused = 0
                    else:
                        logging.info("Player paused")
                        self.paused = 1
                        self.pause_start = time.time()
            elif event.type == pygame.MOUSEBUTTONUP:
                if self.btn_settings.collidepoint(
                        event.pos) and self.paused:
                    self.stage = 'settings'
            elif event.type == self.event_log and not self.paused:
                self.log()
            elif event.type == self.event_warn:
                self.play_sounds()
            elif event.type == self.event_toggletext:
                if self.paused:
                    self.paused += 1
                    if self.paused >= 4:
                        self.paused = 1
        self.get_tick_values()
    GAME_STAGES[1] = main_screen
    GAME_LOOPS[1] = game_loop_main

    def end_screen(self):
        """Activate the end screen. Stage=2"""
        pygame.mixer.music.fadeout(10000) # Fades out over 10 seconds
        self.music_playing = None
    def game_loop_end(self):
        """One iteration of the end screen loop."""
        self.draw_text(self.exit_title,
                       (self.size[0]/37.6, self.height*5/192),
                       mode='topleft', color_id='white', font_id='large')
        self.draw_text(self.exit_reason,
                       (self.size[0]/37.6, self.height*17/192),
                       mode='bottomleft', color_id='white')
        btn_reset = pygame.rect.Rect(
                self.x + self.width*5/256, self.y + self.height*21/192,
                self.width / 6, self.height / 24)
        pygame.draw.rect(self.screen, self.colors['panel'], btn_reset)
        self.draw_text("Play Again", btn_reset.center, color_id='white')
        pygame.display.flip()
        for event in self.events:
            if event.type == pygame.MOUSEBUTTONUP:
                if btn_reset.collidepoint(event.pos):
                    self.reset()
                    self.stage = 1
    GAME_STAGES[2] = end_screen
    GAME_LOOPS[2] = game_loop_end
