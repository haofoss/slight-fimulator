#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""Slight Fimulator - Flight simlator in Python
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


BUG REPORTS
FIXED: nav text doesn't appear above objectivemarker
FIXED: if altitude +/- 500 objectivealtitude, play sound_altitude
WONTFIX: Use perspective grid to create images for yoke
WONTFIX: shattered glass transparnt png on crash
WONTFIX: ignore controls if apleveloff == True
TODO: add a blue background to attitude indicator
WONTFIX: add framerate speedup (0.5 for 2x speed). divide every
  action by the speedup rate.
WONTFIX: output a log after flight
WONTFIX: generate a random background of green and blue squares
FIXED: BUG: Damaage has decimal when damaged by overspeed

ALTERNATE NAMES
Glide Slope
Departure As Filed
Hundred Above
Decision Height
Dank Angle
Dlight simulator

SLOGAN
Just a bit of fimulating
"""

import random
import os
import math

import pygame


__author__ = "Hao Tian"
__version__ = "1.0.1"
# Modified 2017-06-16 Hao Tian
# Modified 2017-07-12 Adrien Hopkins


### OS RELATED STUFF
hostos = os.name # read operating system
os.environ['SDL_VIDEO_CENTERED'] = '1' # center the window.
# source: https://stackoverflow.com/questions/5814125/
# how-to-designate-where-pygame-creates-the-game-window

# Gets current filepath
PATH = "%s/Images" % os.path.dirname(os.path.realpath(__file__))

# events
RUN = 10
pygame.time.set_timer(RUN, 1000)

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.init()
pygame.display.set_caption("Slight Fimulator")
screen = pygame.display.set_mode([1280, 940])
gameon=True


### VARIABLES
heading = 0
roll = 0
controlroll = 0
rollchange = 0

pitch = 0
controlpitch = 0

speed = 150
throttle = 40

altitude = 2500
verticalspeed = 0
verticalspeedsec = 0
altimeter = 29.92

apleveloff = False

status = "Fly to the objective."
statuscounter = 0
statuslastmessage = ""

warn = {"terrain": False,
        "terrainloop": False,
        "pullup": False,
        "pulluploop": False,
        "dontsink": False,
        "dontsinkloop": False,
        "overspeed": False,
        "bankangle":False,
        "altitude":False,
        "stall":False
        }

score = 0
damage = 0
exitcode = 0

objectivelocations = [
    [],
    [],
    []
    ]




# functions

def searchsublist(inputlist, searchfor):
    loopnum = 0
    while searchfor != inputlist[loopnum][0]:
        loopnum += 1
    return loopnum

##def searchsublist(inputlist, searchfor, searchforindex=0, returnindex=1):
##    loopnum = 0
##    for i in inputlist:
##        if searchfor == inputlist[loopnum][0]:
##            return inputlist[loopnum][1]
##            break
##    else:
##        print "no match DO NOT UNCOMMENT THIS FUNCTION",
##        print inputlist[loopnum][0], inputlist[loopnum][1]
##        loopnum += 1


def degtopixelchange(heading, speed):
    ## math.sin(math.radians(90)) #returns sin of 90

    xrad = math.radians(heading)
    yrad = math.radians(heading)
    
    x = math.sin(xrad) * speed
    y = math.cos(yrad) * speed

    return x, y

def togglewarnloop(warnvar, loopvar):
    global warn #, warnvar, loopvar
    if warn[loopvar] == True:
        warn[warnvar] = True
        warn[loopvar] = False
    else:
        warn[loopvar] = True


def runwarnings():
    global warn, status, statuscounter
  
    if warn["pullup"]:
        screen.blit(msg_pullup, (200, 490))
        sound_pullup.play()
        warn["pullup"] = False

    elif warn["terrain"]:
        screen.blit(msg_warning, (187, 168))
        sound_terrain.play()
        warn["terrain"] = False

    elif warn["stall"]:
        screen.blit(msg_stall, (33, 491))
        sound_stall.play()
        warn["stall"] = False
      
    elif warn["dontsink"]:
        screen.blit(msg_dontsink, (304, 545))
        sound_dontsink.play()
        warn["dontsink"] = False

    elif warn["bankangle"]:
        screen.blit(msg_bankangle, (32, 545))
        sound_bankangle.play()
        warn["bankangle"] = False

    if warn["overspeed"]:
        screen.blit(msg_overspeed, (365, 490))
        sound_overspeed.play()
        warn["overspeed"] = False
    
    if warn["altitude"]:
        sound_altitude.play()
        warn["altitude"] = False
        

def approachingaltitude(tolerance):
    global objectivealtitude, altitude
##    return ((objectivealtitude - altitude) >= -tolerance
##    or (altitude - objectivealtitude) <= tolerance)
    return abs(objectivealtitude - altitude) <= tolerance


### CONTROLS

# defines which yoke position correlates to vertical speed in feet per second
# in real life this should increase exponentially
pitchresponses = [
                [4, 40],
                [3, 30],
                [2, 20],
                [1, 10],
                [0, 0],
                [-1, -10],
                [-2, -20],
                [-3, -30],
                [-4, -40]
                ]

rollresponses = [
                [4, 30],
                [3, 20],
                [2, 10],
                [1, 5],
                [0, 0],
                [-1, -5],
                [-2, -10],
                [-3, -20],
                [-4, -30]
                ]



# colors
bgcolor = pygame.color.Color("#101031")
panelcolor = pygame.color.Color("#484F63")
black = pygame.color.Color("#000000")
white = pygame.color.Color("#ffffff")
red = pygame.color.Color("#ff0000")
green = pygame.color.Color("#00ff00")
blue = pygame.color.Color("#0000ff")

# panels
panelpfd = pygame.rect.Rect(25, 100, 500, 500)
panelnav = pygame.rect.Rect(555, 25, 710, 710)

# fonts
# use a nonfree font if we are on winnt. otherwise use default.
# WONTFIX: fontlarge is same as font
if hostos == "nt":
    font = pygame.sysfont.SysFont("Lucida Console", 24)
    fontlarge = pygame.sysfont.SysFont("Lucida Console", 24)
    fontlarge2 = pygame.sysfont.SysFont("Lucida Console", 48)
else:
    font = pygame.font.Font(None, 24)
    fontlarge = pygame.font.Font(None, 24)
    fontlarge2 = pygame.sysfont.SysFont(None, 48)

# images
logo = pygame.image.load("%s/Images/logo.png" % PATH)
logo = pygame.transform.scale(logo, (521, 178))
logotext = pygame.image.load("%s/Images/logotext.png" % PATH)
titleprompt = pygame.image.load("%s/Images/titleprompt.png" % PATH)
gameoveroverlay = pygame.image.load("%s/Images/gameoveroverlay.png" % PATH)
yoke4 = pygame.image.load("%s/Images/yoke4.png" % PATH)
yoke3 = pygame.image.load("%s/Images/yoke3.png" % PATH)
yoke2 = pygame.image.load("%s/Images/yoke2.png" % PATH)
yoke1 = pygame.image.load("%s/Images/yoke1.png" % PATH)
yoke0 = pygame.image.load("%s/Images/yoke0.png" % PATH)
yoken1 = pygame.image.load("%s/Images/yoke-1.png" % PATH)
yoken2 = pygame.image.load("%s/Images/yoke-2.png" % PATH)
yoken3 = pygame.image.load("%s/Images/yoke-3.png" % PATH)
yoken4 = pygame.image.load("%s/Images/yoke-4.png" % PATH)

# sounds
sound_pullup = pygame.mixer.Sound("%s/Sounds/sound_pullup.wav" % PATH)
sound_terrain = pygame.mixer.Sound("%s/Sounds/sound_terrain.wav" % PATH)
sound_dontsink = pygame.mixer.Sound("%s/Sounds/sound_dontsink.wav" % PATH)

sound_stall = pygame.mixer.Sound("%s/Sounds/sound_stall.wav" % PATH)
sound_overspeed = pygame.mixer.Sound("%s/Sounds/sound_overspeed.wav" % PATH)
sound_bankangle = pygame.mixer.Sound("%s/Sounds/sound_bankangle.wav" % PATH)
sound_gear = pygame.mixer.Sound("%s/Sounds/sound_gear.wav" % PATH)
 
sound_config = pygame.mixer.Sound("%s/Sounds/sound_config.wav" % PATH)
sound_apdisconnect = pygame.mixer.Sound("%s/Sounds/sound_apdisconnect.wav" % PATH)
sound_altitude = pygame.mixer.Sound("%s/Sounds/sound_altitude.wav" % PATH)

sound_moonbase = pygame.mixer.Sound("%s/Sounds/sound_moonbase.wav" % PATH)


# PFD images and static text
attitudetape = pygame.image.load("%s/Images/attitudetape.png" % PATH)
attitudetapex = 135 # orig: 135, new: -223
attitudetapey = 150 # orig: 150, new: -637
attitudecrosshair = pygame.image.load("%s/Images/attitudecrosshair.png" % PATH)
attituderecttop2 = pygame.rect.Rect(135, 0, 350, 100) # 284
attituderecttop = pygame.rect.Rect(135, 100, 400, 140) #284
attituderectleft = pygame.rect.Rect(135, 150, 50, 350)
attituderectright = pygame.rect.Rect(370, 150, 300, 350)
attituderectright2 = pygame.rect.Rect(524, 50, 49, 800) # outside right edge
attituderectbottom = pygame.rect.Rect(25, 482, 499, 118) 
attituderectbottom2 = pygame.rect.Rect(25, 600, 499, 200)
altitudelabel = font.render("ALTITUDE", 1, white)
damagelabel = font.render("DAMAGE", 1, white)
speedlabel = font.render("SPEED", 1, white)
verticalspeedlabel = font.render("VERT SPD", 1, white)


### COORDINATES
# x, y: used internally to draw the marker
# xuser, yuser: offsetted user-friendly coordinates
#
# FLIGHT AREA
# x: 560 to 1260
# y: 30 to 730

navmarker = pygame.image.load("%s/Images/navmarker.png" % PATH)
objectivemarker = pygame.image.load("%s/Images/objectivemarker.png" % PATH)

x = 963.917941 # x = 891 for center
y = 430.6969420



def generateobjective(objectivealtituderangemin, objectivealtituderangemax):
    """calculates coordinates and altitude of objective"""
    global objectivex, objectivey, objectivealtitude, withinobjectiverange
    global navmarker, navmarkerrect, objectivemarker, objectivemarkerrect
    
    objectivex = 0
    objectivey = 0
    objectivealtitude = 0
    withinobjectiverange = False

    navmarkerrect = navmarker.get_rect()
    navmarkerrect.x = x
    navmarkerrect.y = y
    objectivemarkerrect = objectivemarker.get_rect()
    objectivemarkerrect.x = objectivex
    objectivemarkerrect.y = objectivey

    # generate objectivex and objectivey
    # while navmarker collides with objectivemarker,
    # or objective coordinates aren't in range
    while (navmarkerrect.colliderect(objectivemarkerrect) == True or
          (objectivex > 700 and objectivex < 1100) == False or
          (objectivey > 130 and objectivey < 640) == False):
        
        objectivex= random.random() * 1000
        objectivey = random.random() * 1000

        navmarkerrect = navmarker.get_rect()
        navmarkerrect.x = x
        navmarkerrect.y = y

        objectivemarkerrect = objectivemarker.get_rect()
        objectivemarkerrect.x = objectivex
        objectivemarkerrect.y = objectivey

    objectivealtitude = random.randrange(objectivealtituderangemin,
            objectivealtituderangemax) 


# set coordinates of the initial objective
generateobjective(3000, 7000)

# calculate user-friendly coordinates
xuser = x - 350
yuser = y - 10
objectivexuser = objectivex - 350
objectiveyuser = objectivey - 10



# NAV images and static text
navarea = pygame.rect.Rect(560, 30, 700, 700)
navcircle = pygame.image.load("%s/Images/navcircle.png" % PATH)
locationlabel = font.render("LOCATION", 1, white)
throttlelabel = font.render("THR", 1, white)
throttlerect100 = pygame.rect.Rect(155, 380, 20, 100)
throttlerect130 = pygame.rect.Rect(155, 350, 20, 130)

# warnings
msg_apengaged = pygame.image.load("%s/Images/msg_apengaged.png" % PATH)
msg_apdisconnect = pygame.image.load("%s/Images/msg_apdisconnect.png" % PATH)
msg_bankangle = pygame.image.load("%s/Images/msg_bankangle.png" % PATH)
msg_over_g = pygame.image.load("%s/Images/msg_over_g.png" % PATH)
msg_overspeed = pygame.image.load("%s/Images/msg_overspeed.png" % PATH)
msg_stall = pygame.image.load("%s/Images/msg_stall.png" % PATH)
msg_pullup = pygame.image.load("%s/Images/msg_pullup.png" % PATH)
msg_warning = pygame.image.load("%s/Images/msg_warning.png" % PATH)
msg_dontsink = pygame.image.load("%s/Images/msg_dontsink.png" % PATH)
msg_terrain = pygame.image.load("%s/Images/msg_terrain.png" % PATH)

startupmsg = """
Slight Fimulator Copyright (C) 2017 Hao Tian
This program comes with ABSOLUTELY NO WARRANTY
This is free software, and you are welcome to redistribute it
under certain conditions; see COPYING file
"""


##### TITLE SCREEN ###

print startupmsg

# TODO: does vorbis play on windows?
pygame.mixer.music.load("%s/Sounds/chilled-eks.ogg" % PATH) 
pygame.mixer.music.play(-1)

while True:
    screen.fill(bgcolor)
    screen.blit(logo, ((1280 - logo.get_width()) / 2, 50))
    screen.blit(logotext, ((1280 - logotext.get_width()) / 2, 300))
    screen.blit(titleprompt, (700, 700))
    
    pygame.display.flip()

    keys = pygame.key.get_pressed()
    event = pygame.event.poll()

    if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
        pygame.quit()

    if event.type == pygame.MOUSEBUTTONDOWN:
        break


##### MAIN LOOP ###
pygame.mouse.set_pos(1279, 1023)
pygame.mixer.music.stop()
pygame.mixer.music.load("%s/Sounds/chip-respect.ogg" % PATH)
pygame.mixer.music.play(-1)

while exitcode == 0:
    screen.fill(bgcolor)

    # draw pfd panel
    pygame.draw.rect(screen, panelcolor, panelpfd)
    
    # draw attitude indicator
    attitudetapey = 150 + (controlpitch * 18)
    attitudetaperotated = pygame.transform.rotate(attitudetape, roll)
    screen.blit(attitudetaperotated, (attitudetapex, attitudetapey))
    screen.blit(attitudecrosshair, (173, 362))

    # draw boxes to cover unused parts of attitude indicator
    pygame.draw.rect(screen, bgcolor, attituderecttop2)
    pygame.draw.rect(screen, panelcolor, attituderecttop)
    pygame.draw.rect(screen, panelcolor, attituderectleft)
    pygame.draw.rect(screen, panelcolor, attituderectright)
    pygame.draw.rect(screen, bgcolor, attituderectright2)
    pygame.draw.rect(screen, panelcolor, attituderectbottom)
    pygame.draw.rect(screen, bgcolor, attituderectbottom2)

    # render updateable text
    altitudetext = font.render(str(altitude) + " FT", 1, white)
    damagetext = font.render(str(int(round(damage))) + "%", 1, white)
    speedtext = font.render(str(int(speed)) + " KTS", 1, white)
    verticalspeedtext = font.render(str(verticalspeed) + " FT", 1, white)
    headingtext = font.render("HDG: " + str(heading), 1, white)
    locationxtext = font.render("LAT : %.7f" % xuser, 1, white)
    locationytext = font.render("LONG: %.7f" % yuser, 1, white)
    objectivextext = font.render("X  : " + str(objectivex), 1, white)
    objectivextext = font.render("Y  : " + str(objectivey), 1, white)
    objectivealtitudetext = font.render("OBJ ALT: " + str(objectivealtitude)
            + " FT", 1, white)
    altimetertext = font.render("ALTIMETER: " + str(altimeter), 1, white)
    scoretext = font.render("SCORE: " + str(score), 1, white)


    # draw PFD labels and text
    screen.blit(altitudelabel, (30, 335))
    screen.blit(altitudetext, (30, 360))
    
    screen.blit(damagelabel, (30, 425))
    screen.blit(damagetext, (30, 450))

    # vertical speed bar
    verticalspeedrect = pygame.rect.Rect(375, 365, 20, -verticalspeedsec * 2.8)
    # * 2 for conservative

    # determine color for vertical speed rectangle    
    if verticalspeedsec < 0:
        verticalspeedrectcolor = red
    elif verticalspeedsec > 0:
        verticalspeedrectcolor = green
    else:
        verticalspeedrectcolor = white
        
    pygame.draw.rect(screen, verticalspeedrectcolor, verticalspeedrect)

    screen.blit(speedlabel, (410, 335))
    screen.blit(speedtext, (410, 360))

    screen.blit(verticalspeedlabel, (410, 425))
    screen.blit(verticalspeedtext, (410, 450))

    # throttle bar
    throttlerect = pygame.rect.Rect(155, 480 - throttle, 20, throttle)
    pygame.draw.rect(screen, red, throttlerect130)
    pygame.draw.rect(screen, white, throttlerect100)
    pygame.draw.rect(screen, green, throttlerect)
    screen.blit(throttlelabel, (135, 240))
    throttletext = font.render(str(int(round(throttle))) + "%", 1, white)
    screen.blit(throttletext, (135, 265))

    # draw NAV
    pygame.draw.rect(screen, panelcolor, panelnav)
    pygame.draw.rect(screen, black, navarea)
    screen.blit(navcircle, (560, 30))
    navmarkerrotated = pygame.transform.rotate(navmarker, -heading)

    screen.blit(locationlabel, (572, 651))
    screen.blit(locationxtext, (572, 676))
    screen.blit(locationytext, (572, 702))
    screen.blit(headingtext, (840, 60))
    screen.blit(altimetertext, (1030, 45))
    screen.blit(scoretext, (1030, 70))
    
    screen.blit(objectivemarker, (objectivex, objectivey))
    screen.blit(objectivealtitudetext, (1000, 702))

    screen.blit(navmarkerrotated, (x, y))



    ### CONTROLS    
    event = pygame.event.poll()
    keys = pygame.key.get_pressed()

    # check for autopilot key (Z)
    if keys[pygame.K_z]:
        apleveloff = True
        
    # autopilot warning
    if apleveloff == True:
        screen.blit(msg_apengaged, (170, 110))
        status = "Autopilot engaged..."
    else:
        screen.blit(msg_apdisconnect, (140, 110))
          
    
    if event.type == RUN:

        ### CONTROLS FOR PITCH ###
        # WONTFIX: vertical speed is unaffected by airspeed

        # pitch up
        if keys[pygame.K_DOWN]:
            if controlpitch < 4:
                controlpitch += 1 # increase yoke
                verticalspeedsec = pitchresponses[searchsublist(pitchresponses, controlpitch)][1] # get vertical speed for this yoke position

        # pitch down  # TODO: Change to elif?
        if keys[pygame.K_UP]:
            if controlpitch > -4:
                controlpitch -= 1 # decrease yoke
                verticalspeedsec = pitchresponses[searchsublist(pitchresponses, controlpitch)][1] # get vertical speed for this yoke position

        altitude += verticalspeedsec # apply vertical speed


        ### CONTROLS FOR ROLL ###
        # TODO: use "roll" and "rollchange". add rollchange to total roll,
        # so aircraft can be rolled infinitely. wrap around at 360.
        
        # roll right
        if keys[pygame.K_RIGHT]:
            if controlroll < 4:
                controlroll += 1 # increase roll
                roll = rollresponses[searchsublist(rollresponses,
                        controlroll)][1]
                # get degree of bank for this yoke position

        # roll left  # TODO: change to elif?
        if keys[pygame.K_LEFT]:
            if controlroll > -4:
                controlroll -= 1 # decrease roll
                roll = rollresponses[searchsublist(rollresponses,
                        controlroll)][1]
                # get degree of bank for this yoke position

        # compass degree wrap around
        if (heading + roll) < 0: # wrap around from 0 to 359
            offset  = heading + roll
            heading = 360 + offset
        elif (heading + roll) >= 360: # wrap around from 359 to 0
            offset = 360 - heading
            heading = roll - offset
        else: # wrap around not necessary, just add heading normally
            heading += roll

        ### LEVEL OFF ###
        # centers controls if apleveloff is engaged
        if apleveloff == True:
            if controlpitch > 0:
                controlpitch -= 1
            elif controlpitch < 0:
                controlpitch += 1

            # TODO: to make this faster, change roll to controlroll,
            # += 1, -= 1.
            if roll > 10:
                roll -= 10
            elif roll > 0:
                roll -= 1
            elif roll < -10:
                roll += 10
            elif roll < 0:
                roll += 1

            # if throttle percentage is odd, add 1% to make it even
            if throttle % 2 == 1:
                throttle += 1

            # set throttle to 40%
##            if throttle == 40:
##                pass
            if throttle < 30:
                throttle += 10
            elif throttle < 40:
                throttle += 2
            elif throttle > 50:
                throttle -= 10
            elif throttle > 40:
                throttle -= 2
            
            if controlpitch == 0 and roll == 0 and throttle == 40:
                controlroll = 0
                verticalspeedsec = 0
                apleveloff = False
                sound_apdisconnect.play()
        
        ### THROTTLE
        # manages speed, throttle, throttlechange
        
        if keys[pygame.K_F2]:
            throttle -= 4 # F2 throttle step
        if keys[pygame.K_F3]:
            throttle += 4 # F3 throttle step
        if keys[pygame.K_F1]:
            throttle = 0
        if keys[pygame.K_F4]:
            throttle = 100


        # accumulate damage
        if throttle > 100:
            damage += (throttle - 100) * 0.01

        # reset throttle to allowed values if exceeded
        if throttle < 0:
            throttle = 0
        if throttle > 130:
            throttle = 130
        
        if speed <= 120:
            speed += (throttle - 60) * 0.4
        elif speed <= 280:
            speed += (throttle - 60) * 0.13
        elif speed <= 340:
            speed += (throttle - 60) * 0.05
        else:
            speed += (throttle - 60) * 0.01


        ### WARNINGS
        
        # warn overspeed
        if speed >= 295:
            status = "Hold F2 key to reduce throttle!"
            damage += (speed - 100) * 0.01
            warn["overspeed"] = True
        
        # warn bank angle
        if roll >= 30 or roll <= -30:
            warn["bankangle"] = True
            
        
            #TODO: still need to add in these warnings
    ##    screen.blit(msg_over_g, (0, 96))
    
        # pull up too low
        if altitude <= 500:
            if warn["pulluploop"] == True:
                warn["pullup"] = True
                warn["pulluploop"] = False
            else:
                warn["pulluploop"] = True
            status = "PRESS AND HOLD THE \"DOWN\" KEY!"

        # don't sink
        elif altitude < 2000 and verticalspeed > 0 and (throttle > 40):            
            togglewarnloop("dontsink", "dontsinkloop")
            status = "Be careful not to stall."
            
        # too low terrain
        elif altitude < 2000 and verticalspeedsec >= -20:
            # and (throttle <= 40):
            if warn["terrainloop"] == True:
                warn["terrain"] = True
                warn["terrainloop"] = False
            else:
                warn["terrainloop"] = True
                

        # pull up fast descent
        elif altitude < 2000 and verticalspeedsec < -20:
            if warn["pulluploop"] == True:
                warn["pullup"] = True
                warn["pulluploop"] = False
            else:
                warn["pulluploop"] = True
            status = "DO NOT DESCEND!"



        # if we are in objective altitude range
        elif approachingaltitude(1000):
            status = "Approaching objective altitude..."

            # if we just entered objective altitude range
            if withinobjectiverange == False:
                warn["altitude"] = True
                withinobjectiverange = True

        # if we are outside objective altitude range
        elif approachingaltitude(1000) == False:
            withinobjectiverange = False
                


        runwarnings()

        ### OBJECTIVE
        
        # check for collision with objective

        navmarkerrect = navmarker.get_rect()
        navmarkerrect.x = x
        navmarkerrect.y = y
        
        objectivemarkerrect = objectivemarker.get_rect()
        objectivemarkerrect.x = objectivex
        objectivemarkerrect.y = objectivey

        # check for alttiude with 800 ft tolerance
        if navmarkerrect.colliderect(objectivemarkerrect):
            if approachingaltitude(800):
                score += 1
                generateobjective(10000, 23000)
                status = "New objective received."
                if score == 10:
                    exitcode = 1
            else:
                status = "Objective NOT complete. Check OBJ ALT"


        ### EVENTS


        # stalling
        if speed <= 60:
            # stall warning
            warn["stall"] = True

        # stall
        if speed <= 40:
            altitude -= 200
            # force pitch down
            if controlpitch > 0:
                controlpitch -= 1            
        
        # don't let speed enter negatives
        if speed <= 0:
            speed = 0

        # update aircraft speed if we're not stalling
        if speed > 40:
            # update navmarker location
            xchange, ychange = degtopixelchange(heading, speed / 100)
            x += xchange
            y -= ychange


##        # clear status once every 7 turns
##        statuscounter += 1
##        
##        if status == statuslastmessage:
##            statuscounter += 1
##        
##        if statuscounter >= 6:
##            status = ""
##            statuslastmessage = ""
##            statuscounter = 0
##            
##        statuslastmessage = status

        # check for crash
        if altitude <= 0:
            screen.blit(gameoveroverlay, (0, 0))
            randomstatus = random.randrange(1, 20)
            
            if randomstatus == 1:
                status = "Vultures eat your corpse"
            else:
                status = "CRASH"
                
            exitcode = 3

        if altitude >= 41450:
            exitcode = 6

        # check for collision with square borders
        if y <= 30 or y >= 686 or x <= 548:
            exitcode = 4

        # check for damage
        if damage >= 100:
            status = "Aircraft overstressed!"
            exitcode = 5


        
        ### UPDATE VARIABLES
        verticalspeed = verticalspeedsec * 60 # calculate vertical speed,
        # which is displayed on PFD
        xuser = x - 350
        yuser = y - 10

        # draw status text
        statustext = fontlarge.render(status, 1, white)
        screen.blit(statustext, (25, 700))
        
        print "HDG:" + str(heading) + " ALT:" + str(altitude) + " VS:" \
                + str(verticalspeedsec) + " CP:" + str(controlpitch) \
                + " R:" + str(roll) + " CR:" + str(controlroll) + " X:" \
                + str(x) + " Y:" + str(y)

        # update screen once every second so warnings work
        pygame.display.flip()

##    # update the screen very often
##    pygame.display.flip()
    
    
    if event.type == pygame.QUIT:
        exitcode = 2
        

print "[!] Exited main loop with exitcode " + str(exitcode)
pygame.time.delay(4000)

# EXIT CODES
# 0: unexpected
# 1: game complete
# 2: clicked quit
# 3: crash on ground
# 4: left the flight area
# 5: engine damage 100%
# 6: service ceiling altitude exceeded

exittitles = [
                "UNEXPECTED",
                "Congratulations",
                "Closed",
                "Failed",
                "Failed",
                "Failed",
                "Failed",
                "UNEXPECTED"
                ]
exitreasons = [
                "Exited with exitcode 0 (unexpected). Please report.",
                "You have completed the objective with a score of %i." % score,
                "The game has been closed. Your score was %i." % score,
                "You crashed your aircraft. Your score was %i." % score,
                "Left the operation area. Your score was %i." % score,
                "The aircraft was overstressed. Your score was %i." % score,
                "The aircraft exceeded its service ceiling altitude. \
Your score was %i." % score,
                "Exited with exitcode 7 (unexpected). Please report."
                ]

exittitle = fontlarge2.render(exittitles[exitcode], 1, white)
exittext = font.render(exitreasons[exitcode], 1, white)

status = "You may now close the program."
statustext = fontlarge.render(status, 1, white)
pygame.mouse.set_pos(1280, 0)

if exitcode == 1:
    # do these if the player wins
    pygame.mixer.music.stop()
    sound_moonbase.play()
    pygame.mixer.music.play(-1)

while True:
    screen.fill(bgcolor)
    screen.blit(exittitle, (25, 0))
    screen.blit(exittext, (25, 100))

    statustext = fontlarge.render(status, 1, white)
    screen.blit(statustext, (25, 700))

    
    pygame.display.flip()
    event = pygame.event.poll()
    if event.type == pygame.QUIT:
        break
pygame.quit()
