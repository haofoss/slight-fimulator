#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""Code for game objects."""

import zipfile
import io
import os

import pygame


class Game(object):
    """A object that can be used to make a game."""
    BG_PRESETS = {
        'white': {'type': "color", 'color': "#FFFFFF"},
        'black': {'type': "color", 'color': "#000000"},
        'bg-color': {'type': 'color', 'name': "background"},
        'image': {'type': "image", 'name': "background", 'tile': False}
    }
    def __init__(self, title="pygame window", icontitle="pygame window",
            resources_path='resources.zip', size=(640, 480),
            bg=BG_PRESETS['white'], fps_max=60, **kw):
        """Initializes the instance."""
        self.size = size
        self.clock = pygame.time.Clock() # Controls ticking
        self.fps_max = fps_max # Controls max fps

        self.resources_path = resources_path
        self.bg = bg
        
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption(title, icontitle)

    def __repr__(self):
        """Prints all of the variables."""
        return str(self.__dict__)

    def load_resources(self):
        """Loads the game's resources. Compatible with zips.

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

        Adds three default fonts if none are provided.
        If font size is a decimal, multiplies font size by the window's height
         (this includes numbers ending in .0)
        Any line in fonts.txt or colors.txt that starts with a # is ignored
        Blank lines are also ignored
        """
        self.images = {}
        self.sounds = {}
        self.music_files = {}
        self.colors = {}
        self.fonts = {}
        if self.resources_path.endswith('.zip'):
            # Zip Archive Found!
            self.resources = zipfile.ZipFile(self.resources_path)
            for filename in self.resources.namelist():
                if filename.endswith('/'):
                    pass # Is a folder, don't extract
                elif filename.startswith('Images/'):
                    image_data = self.resources.read(filename)
                    image_bytes_io = io.BytesIO(image_data)
                    image = pygame.image.load(image_bytes_io)
                    image_name = \
                            filename.lower() [7:].split('.') [0]
                    self.images[image_name] = image
                elif filename.startswith('Sounds/'):
                    sound_data = self.resources.read(filename)
                    sound_bytes_io = io.BytesIO(sound_data)
                    sound = pygame.mixer.Sound(sound_bytes_io)
                    sound_name = \
                            filename.lower() [7:].split('.') [0]
                    self.sounds[sound_name] = sound
                elif filename.startswith('Music/'):
                    music_data = self.resources.read(filename)
                    music_bytes_io = io.BytesIO(music_data)
                    music_name = \
                            filename.lower() [6:].split('.') [0]
                    self.music_files[music_name] = music_bytes_io
                elif filename in ['colors.txt', 'colours.txt']:
                    colors_file = self.resources.open(filename)
                    for line in colors_file.readlines():
                        line = str(line.decode('utf-8'))
                        if line.strip() == '': continue
                        elif line.strip() [0] == '#': continue
                        colorname, color = line.split('=')
                        colorname = colorname.strip()
                        color = pygame.color.Color(color.strip())
                        self.colors[colorname] = color
                elif filename == 'fonts.txt':
                    fonts_file = self.resources.open(filename)
                    for line in fonts_file.readlines():
                        line = str(line.decode('utf-8'))
                        if line.strip() == '': continue
                        elif line.strip() [0] == '#': continue
                        fontname, font = line.split('=')
                        fontname = fontname.strip()
                        font_info = font.strip().split(' ')
                        font = ' '.join(font_info[:-1])
                        size = font_info[-1]
                        if '.' in size: size = int(float(size) * self.size[1])
                        else: size = int(size)
                        if font.lower() in ['none', 'default']:
                            font = None
                        font = pygame.font.Font(font, size)
                        self.fonts[fontname] = font
        else: # Not a zip
            images_path = "%s/Images" % self.resources_path
            for image_name in os.listdir(images_path):
                image_file = "%s/%s" % (images_path, image_name)
                image_name = image_name.split('.') [0]
                image = pygame.image.load(image_file)
                self.images[image_name] = image
            sounds_path = "%s/Sounds" % self.resources_path
            for sound_name in os.listdir(sounds_path):
                sound_file = "%s/%s" % (sounds_path, sound_name)
                sound_name = sound_name.split('.') [0]
                sound = pygame.mixer.Sound(sound_file)
                self.sounds[sound_name] = sound
            music_path = "%s/Music" % self.resources_path
            for music_name in os.listdir(music_path):
                music_file = "%s/%s" % (music_path, music_name)
                music_name = music_name.split('.') [0]
                self.music_files[music_name] = music_file
            if "colors.txt" in os.listdir(self.resources_path):
                colors_file = open("%s/colors.txt" % self.resources_path, 'rt')
            elif "colours.txt" in os.listdir(self.resources_path):
                colors_file = open("%s/colours.txt" % self.resources_path,
                        'rt')
            else: colors_file = None
            if colors_file != None:
                for line in colors_file.readlines():
                    if line.strip() == '': continue
                    elif line.strip() [0] == '#': continue
                    colorname, color = line.split('=')
                    colorname = colorname.strip()
                    color = pygame.color.Color(color.strip())
                    self.colors[colorname] = color
            try:
                fonts_file = open("%s/fonts.txt" % self.resources_path)
                for line in fonts_file.readlines():
                    if line.strip() == '': continue
                    elif line.strip() [0] == '#': continue
                    fontname, font = line.split('=')
                    fontname = fontname.strip()
                    font_info = font.strip().split(' ')
                    font = ' '.join(font_info[:-1])
                    size = font_info[-1]
                    if '.' in size: size = int(float(size) * self.size[1])
                    else: size = int(size)
                    if font.lower() in ['none', 'default']:
                        font = None
                    font = pygame.font.Font(font, size)
                    self.fonts[fontname] = font
            except Exception as e: print(e)
        if self.fonts == {}:
            self.fonts['default'] = pygame.font.Font(None, self.size[1]/20)
            self.fonts['small'] = pygame.font.Font(None, self.size[1]/40)
            self.fonts['large'] = pygame.font.Font(None, self.size[1]/10)
                    

    def startup(self):
        """A \"hook\" function to use for variable creation.

        It is called once at the beginning of the program."""
        pass

    def draw_bg(self):
        """Draws the background.  Can be overrided if nescesary."""
        if self.bg['type'] == "color":
            if 'name' in self.bg.keys():
                self.screen.fill(self.colors[self.bg['name']])
            else: self.screen.fill(pygame.color.Color(self.bg['color']))
        elif self.bg['type'] == "image":
            if 'tile' not in self.bg.keys(): self.bg['tile'] = False
            if self.bg['tile']:
                for x in range(self.size[0] / bg_image.get_width() + 1):
                    for y in range(self.size[1] / bg_image.get_height() + 1):
                       self.screen.blit(self.images[self.bg['name']],
                                (bg_image.get_rect().width*x,
                                bg_image.get_rect().height*y))
            else:
                bg_image = pygame.transform.scale(self.images[self.bg['name']],
                        self.size)
                self.screen.blit(bg_image, (0, 0))

    def game_loop(self, *args, **kw):
        """A \"hook\" function to use for one iteration of the game loop.

        It is called every iteration of the while loop.
        The default code is to be used as a template."""
        pygame.display.flip()  
        for event in self.events:
            if event.type == pygame.QUIT:
                return True

    def draw_text(self, text, x, y=None, mode="center", color_id=(0, 0, 0),
            font_id='default', antialias=1, bg_color=None):
        """Draws text \"text\" at x, y."""
        if y == None: x, y = x
        if color_id in self.colors.keys(): color = self.colors[color_id]
        else: color = color_id
        if type(color) == str: color = pygame.color.Color(color)
        elif type(color) == tuple or type(color) == list:
            if len(color) == 3:
                r, g, b = color
                color = pygame.color.Color(r, g, b)
            elif len(color) == 4:
                r, g, b, a = color
                color = pygame.color.Color(r, g, b, a)
        if type(bg_color) == str:
            bg_color = pygame.color.Color(bg_color)
        elif type(bg_color) == tuple or type(bg_color) == list:
            if len(bg_color) == 3:
                r, g, b = bg_color
                bg_color = pygame.color.Color(r, g, b)
            elif len(bg_color) == 4:
                r, g, b, a = bg_color
                bg_color = pygame.color.Color(r, g, b, a)
        if font_id in self.fonts.keys(): font = self.fonts[font_id]
        else: # no font found
            try:
                font_info = font_id.strip().split(' ')
                font = ' '.join(font_info[:-1])
                size = font_info[-1]
                if '.' in size: size = float(size) * self.size[1]
                else: size = int(size)
                if font.lower() in ['none', 'default']:
                    font = None
                font = pygame.font.Font(font, size)
            except:
                raise ValueError("Invalid font %s" % font_id)
        text_obj = font.render(text, antialias, color)
        text_rect = text_obj.get_rect()
        setattr(text_rect, mode, (x, y))
        if bg_color: pygame.draw.rect(self.screen, bg_color, text_rect)
        self.screen.blit(text_obj, text_rect)

    def draw_sprite(self, sprite):
        try: sprite.draw(self.screen)
        except: self.screen.blit(sprite.image, sprite.rect)

    def mainloop(self, *args, **kw):
        """The program's main loop.  Does not need to be overwritten."""
        pygame.init()
        self.load_resources()
        self.startup(*args, **kw)
        while 1: # game loop
            # manages fps
            self.clock.tick(self.fps_max)
            self.fps = self.clock.get_fps()
            self.draw_bg() # draws background
            self.events = pygame.event.get()
            if self.game_loop(*args, **kw): break # does game loop and exiting
        pygame.quit()
        if self.resources_path.endswith('.zip'): self.resources.close()
