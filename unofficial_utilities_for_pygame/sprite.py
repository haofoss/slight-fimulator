#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""Code for sprites."""

import pygame


class ImprovedSprite(pygame.sprite.Sprite):
    """A better sprite with more functionallity and simplicity."""
    def __init__(self, image, x, y=None, velocity=[0, 0]):
        """Initializes the sprite."""
        super(ImprovedSprite, self).__init__()
        # Allows many argument formats
        if y == None: x, y = x
        if type(image) == str: image = pygame.image.load(image)
        # Assigns the attributes
        self.image = image
        self.rect = image.get_rect()
        self.rect.center = x, y
        self.velocity = velocity

    def draw(self, screen):
        """Draws the improved sprite."""
        screen.blit(self.image, self.rect)

    def move(self, motion=None, collide_group=None, collide_mode=None,
            size=None, constrain_mode=None):
        """Moves the sprite with motion. Motion defaults to self.velocity.

        If collide_group is specified, collides with all mombers of it.
            If collide_mode is \"kill\", kills al sprites that collide with
            it.  Otherwise, bounces off them
        If collide_mode is a function, a collision executes it.

        If size is specified (either 2 numbers OR a Surface(), it will
            check for being out of bounds.
        If size != None, returns a tuple.  Each number represents
            x and y, and they are if in bounds,
            1 or -1 if partially out of bounds and 2 or -2 if fully out of bounds.
            The sign depends on direction (- is for left and top; + is for
            right and bottom).
        If constaarin_mode is "bounce" or 1, it will "bounce" off the edge,
            using self.speed.
        If constrain_mode is "wrap" or 2, it will wrap "through" the edge.
        If constrain_mode is "kill" or 3, it will kill the sprite when fully
            out of bounds.
        If constrain_mode is a function, executes it with the
            out-of-bounds tuple."""
        def f(): pass # Gets an empty function for type()
        # Collisions
        if collide_group != None:
            collisions = pygame.sprite.spritecollide(self, collide_group,
                    collide_mode == "kill" or collide_mode == 1)
            if collisions and (collide_mode == "bounce" or collide_mode == 2):
                velocity_mult = [-1, -1]
                for collide in collisions:
                    if (collide.rect.left <= self.rect.left
                            and collide.rect.right >= self.rect.right) \
                            or (self.rect.left <= collide.rect.left
                            and self.rect.right >= collide.rect.right):
                        velocity_mult[0] = 1
                    if (collide.rect.top <= self.rect.top
                            and collide.rect.bottom >= self.rect.bottom) \
                            or (self.rect.top <= collide.rect.top
                            and self.rect.bottom >= collide.rect.bottom):
                        velocity_mult[1] = 1
                self.velocity[0] *= velocity_mult[0]
                self.velocity[1] *= velocity_mult[1]
            elif collisions and type(collide_mode) == type(f):
                for collision in collisions:
                    collide_mode(collision)
            
        # Handles out of bounds, if size is not None
        if size != None:
            if type(size) == pygame.Surface: size = size.get_rect().size
            out_of_bounds = [0, 0]
            rect = self.rect
            # left
            if rect.right < 0: out_of_bounds[0] = -2 # fully out of bounds
            elif rect.left <= 0: out_of_bounds[0] = -1 # partially out of bounds
            # right
            if rect.left > size[0]: out_of_bounds[0] = 2 # fully out of bounds
            elif rect.right >= size[0]: out_of_bounds[0] = 1 # partially O.O.B.
            # up
            if rect.bottom < 0: out_of_bounds[1] = -2 # fully out of bounds
            elif rect.top <= 0: out_of_bounds[1] = -1 # partially out of bounds
            # down
            if rect.top > size[1]: out_of_bounds[1] = 2 # fully out of bounds
            elif rect.bottom >= size[1]: out_of_bounds[1] = 1 # partially O.O.B.
            # handles out of bounds
            if out_of_bounds != [0, 0]:
                if constrain_mode == "bounce" or constrain_mode == 1:
                    if out_of_bounds[0]: self.velocity[0] *= -1
                    if out_of_bounds[1]: self.velocity[1] *= -1
                elif constrain_mode == "wrap" or constrain_mode == 2:
                    if out_of_bounds[0] == 2:
                        self.rect.centerx -= size[0]
                        self.recr.centerx -= self.width
                    elif out_of_bounds[0] == -2:
                        self.rect.centerx += size[0]
                        self.recr.centerx += self.width
                    if out_of_bounds[1] == 2:
                        self.rect.centery -= size[1]
                        self.recr.centery -= self.height
                    elif out_of_bounds[1] == -2:
                        self.rect.centery -= size[1]
                        self.recr.centery -= self.height
                elif constrain_mode == "kill" or constrain_mode == 3:
                    if abs(out_of_bounds[0]) == 2 \
                            or abs(out_of_bounds[1]) == 2:
                        self.kill()
                elif type(constrain_mode) == type(f):
                    constrain_mode(tuple(out_of_bounds))
            
        # Moves the sprite
        if motion == None: motion = self.velocity
        self.rect.move_ip(motion)
        # Return important info
        return_values = {}
        if collide_group != None: return_values['collisions'] = collisions
        if size != None: return_values['out of bounds'] = out_of_bounds
        return return_values

    def accelerate(self, accelx, accely=None, mode="add"):
        """Increases or decreases the sprite's velocity."""
        if accely == None and (type(accelx) == tuple or type(accelx) == list):
            accelx, accely = accelx
        if mode == "add" or mode == 0:
            self.velocity[0] += accelx
            self.velocity[1] += accely
        elif mode == "mult" or mode == 1:
            self.velocity[0] *= accelx
            if accely != None: self.velocity[1] *= accely
            else: self.velocity[1] *= accelx


    def update_(self, screen, collisions=None,
            collide_mode=None, constrain_mode=None, *args, **kw):
        """Updates the sprite.  Can be used with group.update().

        To use, do "self.update = <module-name>.ImprovedSprite.update_
        Returns information about what happened during the update."""
        return_values = {}
        if move: return_values['move'] = self.move(None, collisions,
                collide_mode, screen, constrain_mode)
        if screen != None: return_values['draw'] = self.draw(screen)
        return_values['update'] = self.update_(*args, **kw)
        return return_values


class RectSprite(ImprovedSprite):
    """A sprite that uses a rectangular surface as its \"image]"."""
    def __init__(self, x, y=None, w=None, h=None, color=(0, 0, 0),
            velocity=[0, 0]):
        """Initializes the instance."""
        if y == None: x, y, w, h = x
        surface = pygame.Surface((w, h))
        surface.fill(color)
        super(RectSprite, self).__init__(surface.convert(), x, y, velocity)
        if type(color) == str: color = pygame.color.Color(color)
        elif type(color) == tuple or type(color) == list:
            if len(color) == 3:
                r, g, b = color
                color = pygame.color.Color(r, g, b)
            elif len(color) == 4:
                r, g, b, a = color
                color = pygame.color.Color(r, g, b, a)
        self.color = color


class Button(pygame.rect.Rect):
    """A clickable button with text.

    x, y, w and h work the same way as a pygame.rect.Rect.
    text is text to be printed.
    function is a function to be called when the button is pressed.
    color is the backgorund color, and color_text is the text color.
    Any function doable to pygame.rect.Rect is doable to the Button."""
    def __init__(self, x, y, w, h, text='', font_=None, font_size=36,
            command=None, color="#F0F0F0", color_text="#000000",
            color_outline="#000000"):
        """Initializes the instance."""
        super(Button, self).__init__(x, y, w, h)
        # Allows colors to be in hex, tuple or Color() form
        if type(color) == str: color = pygame.color.Color(color)
        elif type(color) == tuple or type(color) == list:
            if len(color) == 3:
                r, g, b = color
                color = pygame.color.Color(r, g, b)
            elif len(color) == 4:
                r, g, b, a = color
                color = pygame.color.Color(r, g, b, a)
        if type(color_text) == str:
            color_text = pygame.color.Color(color_text)
        elif type(color_text) == tuple or type(color_text) == list:
            if len(color_text) == 3:
                r, g, b = color_text
                color_text = pygame.color.Color(r, g, b)
            elif len(color_text) == 4:
                r, g, b, a = color_text
                color_text = pygame.color.Color(r, g, b, a)
        if type(color_outline) == str:
            color_outline = pygame.color.Color(color_outline)
        elif type(color_outline) == tuple or type(color_outline) == list:
            if len(color_outline) == 3:
                r, g, b = color_outline
                color_outline = pygame.color.Color(r, g, b)
            elif len(color_outline) == 4:
                r, g, b, a = color_outline
                color_outline = pygame.color.Color(r, g, b, a)
        self.text = text
        self.color = color
        self.color_text = color_text
        self.color_outline = color_outline
        self.font = pygame.font.Font(None, font_size)
        self.command = command

    def draw(self, screen, pressed=False):
        """Draws the button on surface screen."""
        if self.color != None:
            pygame.draw.rect(screen, self.color, self)
        if self.color_outline != None:
            pygame.draw.rect(screen, self.color_outline, self, 2)
        if self.color_text != None:
            txt = self.font.render(self.text, 1, self.color_text)
            text_rect = txt.get_rect()
            text_rect.center = self.center
            screen.blit(txt, text_rect)

    def is_pressed(self, x='mouse', y=None):
        """Returns 1 if the button is presses, 0 otherwise.

        It is recommended to put this in pygame.MOUSEBUTTONDOWN."""
        if x == 'mouse': x, y = pygame.mouse.get_pos()
        elif y == None and x != None: x, y = x
        if x != None: return self.collidepoint(x, y)

    def update(self, screen=None, pos='mouse', *args, **kw):
        """Updates the button.

        Draws the button on screen.
        Uses pos to detect if the button is pressed.
        If the button is pressed, calls its command() with args and kw."""
        def f(): pass # Empty function for type
        if type(screen) == pygame.surface.Surface: self.draw(screen)
        if self.command:
            if self.is_pressed():
                self.command(*args, **kw)
        return self.is_pressed(pos)
