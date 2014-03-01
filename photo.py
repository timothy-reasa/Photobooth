#!/usr/bin/env python
# Raspberry Pi PhotoBooth by Bret Lanuis
# Discovered at http://www.raspberrypi.org/phpBB3/viewtopic.php?f=41&t=48232
# Modified by Tim Reasa (timothy.reasa@gmail.com)
# Using Pi Camera Module
# Requires PIL and picamera libraries
# http://github.com/waveform80/picamera
# Pythonware.com/products/pil

import os, sys
import picamera
import time
import Tkinter as tk
from PIL import Image,ImageDraw
from PIL.ImageTk import PhotoImage
import RPi.GPIO as gpio

#Declare constants
BTN_SHUTDOWN = 4
BTN_PHOTO = 22
OUT_LIGHT = 17
OUT_WARNING = 0

DELAY_MS = 100
NUM_IMAGES = 4
MAX_PRINTS = 25

SCREEN_WIDTH = 1680
SCREEN_HEIGHT = 1050
CAMERA_WIDTH = 1200
CAMERA_HEIGHT = 800

DIR_SAVE = "/home/pi/Photobooth/captured_images/"	#for individual camera snapshots
DIR_COMPOSITE = "/home/pi/Photobooth/final_images/" #for final composite images for printing
DIR_IMAGE = "/home/pi/Photobooth/base_images/"		#for static background images

TEST = True #True no printout and shutdown only warns

def shouldShutdown():
    return gpio.input(BTN_SHUTDOWN)
    
def shouldStart():
    return gpio.input(BTN_PHOTO)
        
def lightOn():
    gpio.output(OUT_LIGHT, 1)

def lightOff():
    gpio.output(OUT_LIGHT, 0)
    
def warnOn():
    gpio.output(OUT_WARNING, 1)

def warnOff():
    gpio.output(OUT_WARNING, 0)

def closeProgram(event=None):    
    gpio.cleanup()
    root.destroy()
    return "break"
    
def doShutdown():
    if TEST:
        os.system("sudo shutdown -k now shutdown button pressed [testing]")
    else:
        gpio.cleanup()
        os.system("sudo shutdown -h now shutdown button pressed")
        sys.exit(0)
    
def doPhotoPrint(filename):
    global warn
    global printCount
    if not TEST:
        os.system("lp " + filename)
        printCount += 1
    
    if printCount % MAX_PRINTS == 0:
        warn = True

def takeSinglePhoto(filename, previewLength):
    lightOn()
    camera.hflip = True
    camera.start_preview()
    time.sleep(previewLength)
    camera.hflip = False
    camera.capture(filename)
    camera.stop_preview()
    lightOff()
    
def takePhotos(event=None):
    #Start taking Photos
    today = time.strftime("%d-%m-%Y")
    path = DIR_SAVE + today + "/"
    if not (os.path.isdir(path)):
        os.mkdir(path)
    
    now = time.strftime("%H%M%S")
    for i in range(1, NUM_IMAGES):
        imageName[i] = path + now + "_" + str(i) + ".jpg"
        takeSinglePhoto(imageName[i], 5)
        time.sleep(0.5)

    try:
        for i in range (1, NUM_IMAGES):
            im[i] = Image.open(imageName[i])
    except:
        print "Unable to load individual images"
        exit(1)
     
    try:
        final = Image.open(DIR_IMAGE + "print_background.png")
    except:
        print "Unable to load BG"
        exit(1)

    final.paste(im[1], (30,180))
    final.paste(im[2], (420,180))
    final.paste(im[3], (30,570))
    final.paste(im[4], (420,570))
    
    finalName = DIR_COMPOSITE + now + ".png"
    path = DIR_COMPOSITE + today + "/"
    if not (os.path.isdir(path)):
        os.mkdir(path)
        
    final.save(finalName)
    
    doPhotoPrint(finalName)
    return "break"

def mainBody():

    #First, check for exit conditions
    if shouldShutdown():
        doShutdown()
        
    #Second, check if we should begin photobooth-ing
    if not warn and shouldStart():
	    takePhotos()
	
    #Finally, schedule ourself to run again
    root.after(DELAY_MS, mainBody)
    
#Setup gpio
gpio.setmode(gpio.BCM)
gpio.setup(BTN_SHUTDOWN, gpio.IN)
gpio.setup(BTN_PHOTO, gpio.IN)
gpio.setup(OUT_LIGHT, gpio.OUT)

#Initialize GUI
root = tk.Tk()
root.title("Photobooth")
w = root.winfo_screenwidth()
h = root.winfo_screenheight()
root.overrideredirect(1)
root.geometry(str(SCREEN_WIDTH) + "x" + str(SCREEN_HEIGHT) + "+0+0")

pane = tk.Frame(root)
root.bind("<Escape>", closeProgram)
root.bind("s", takePhotos)
pane.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH) 
bgImage = PhotoImage(file=DIR_IMAGE + "screen_background.png")
bg = tk.Label(pane, image=bgImage)
bg.image = bgImage
bg.pack()
btn1 = tk.Button(pane, text="quit", command=closeProgram)
btn1.place(x=0, y=0)

pane.focus_force()

#Initialize PI camera
camera=picamera.PiCamera()
camera.preview_fullscreen = False
camera.resolution = (CAMERA_WIDTH, CAMERA_HEIGHT)
camera.preview_window = ((SCREEN_WIDTH - CAMERA_WIDTH) / 2, (SCREEN_HEIGHT - CAMERA_HEIGHT) / 3, CAMERA_WIDTH, CAMERA_HEIGHT)
#camera.start_preview()
#camera.color_effects = (128, 128)
#camera.crop = (0.5, 0.5, 1.0, 1.0)

#Initialize state
printCount = 0
warn = 0

#Main loop
root.after(DELAY_MS, mainBody)
root.mainloop()