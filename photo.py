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
import io
import Tkinter
from PIL import Image,ImageDraw
from PIL.ImageTk import PhotoImage
import RPi.GPIO as gpio

class Photobooth(Tkinter.Label):
    #Declare constants
    BTN_SHUTDOWN = 7
    BTN_PHOTO_CLR = 11
    BTN_PHOTO_BW = 12
    #OUT_LIGHT = 15
    #OUT_WARNING = 16

    DELAY_MS = 100
    DELAY_QUIT = 2000
    DELAY_SHUTDOWN = 6000
    
    NUM_IMAGES = 4
    MAX_PRINTS = 25

    SCREEN_WIDTH = 1680
    SCREEN_HEIGHT = 1050
    CAMERA_WIDTH = 1200
    CAMERA_HEIGHT = 800
    PRINT_WIDTH = 930
    PRINT_HEIGHT = 1520
    THUMBNAIL_WIDTH = 430
    THUMBNAIL_HEIGHT = 288
    THUMBNAIL_PADDING = 10
    PRINT_TOP_PADDING = 30

    DIR_SAVE = "/home/pi/Photobooth/captured_images/"	#for individual camera snapshots
    DIR_COMPOSITE = "/home/pi/Photobooth/final_images/" #for final composite images for printing
    DIR_IMAGE = "/home/pi/Photobooth/base_images/"		#for static background images

    TEST = True #True no printout and shutdown only warns

    def shouldShutdown(self):
        #return gpio.input(Photobooth.BTN_SHUTDOWN)
        
    def shouldStartColor(self):
        #return gpio.input(Photobooth.BTN_PHOTO_CLR)
        
    def shouldStartBlackWhite(self):
        #return gpio.input(Photobooth.BTN_PHOTO_BW)
            
    def lightOn(self):
        #gpio.output(Photobooth.OUT_LIGHT, 1)

    def lightOff(self):
        #gpio.output(Photobooth.OUT_LIGHT, 0)
        
    def warnOn(self):
        #gpio.output(Photobooth.OUT_WARNING, 1)

    def warnOff(self):
        #gpio.output(Photobooth.OUT_WARNING, 0)

    def closeProgram(self, event=None):    
        gpio.cleanup()
        self.master.destroy()
        return "break"
        
    def doShutdown(self):
        if self.TEST:
            self.closeProgram()
            
        else:
            gpio.cleanup()
            os.system("sudo shutdown -h now shutdown button pressed")
            sys.exit(0)
        
    def doPhotoPrint(self, filename):

        if not self.TEST:
            os.system("lp " + filename)
            self.printCount += 1
        
        if self.printCount % self.MAX_PRINTS == 0:
            self.warn = True

    def takeSinglePhoto(self, previewLength):
        stream = io.BytesIO()
        
        self.lightOn()
        self.camera.hflip = True
        self.camera.start_preview()
        time.sleep(previewLength)
        self.camera.stop_preview()
        self.camera.hflip = False
        self.camera.capture(stream, format='jpeg')
        self.lightOff()
        
        #It would be nice to display for a few seconds the picture that was just taken
        
        stream.seek(0)
        photo = Image.open(stream)
        return photo
        
    def takePhotos(self, event=None, color=True):
        
        if color:
            self.camera.color_effects = None         #default color
        else:
            self.camera.color_effects = (128, 128)   #black and white
        
        #Start taking photos
        today = time.strftime("%Y-%m-%d")
        path = self.DIR_SAVE + today + "/"
        if not (os.path.isdir(path)):
            os.makedirs(path)
        
        now = time.strftime("%H%M%S")
        
        imageNames = [path + now + "_" + str(i) + ".jpg" for i in range(1, 1 + self.NUM_IMAGES)]
        images = []
        
        #Take photos; save to disk, resize and cache photos
        for imageName in imageNames:
            photo = self.takeSinglePhoto(5)
            photo.save(imageName)
            photo = photo.resize((self.THUMBNAIL_WIDTH,self.THUMBNAIL_HEIGHT), Image.ANTIALIAS)
            images.append(photo)
            time.sleep(0.5)
        
        #Open the final image        
        try:
            final = Image.open(self.DIR_IMAGE + "print_background.png").convert("RGB")
        except:
            print "Unable to load BG"
            exit(1)
        
        #Lay out the photos on the final image
        column1 = self.THUMBNAIL_PADDING
        column2 = self.PRINT_WIDTH - self.THUMBNAIL_PADDING - self.THUMBNAIL_WIDTH
        row = self.THUMBNAIL_PADDING + self.PRINT_TOP_PADDING
        for photo in images:
            final.paste(photo, (column1,row))
            final.paste(photo, (column2,row))
            row += self.THUMBNAIL_HEIGHT + self.THUMBNAIL_PADDING
        
        #Save the final image
        path = self.DIR_COMPOSITE + today + "/"
        finalName = path + now + ".jpg"
        if not (os.path.isdir(path)):
            os.makedirs(path)
            
        final.save(finalName)
        
        self.doPhotoPrint(finalName)
        return "break"
    
    def mainBody(self):
    
        #First, check for exit conditions
        if not self.shouldShutdown():
            if self.willShutDown:       #Wait until the button is released for quit and shutdown
                self.doShutdown()
                return "break"
                
            elif self.willQuit:
                self.closeProgram()
                return "break"
        
            self.buttonCount = 0
            self.willQuit = False
            self.willShutDown = False
            
        else:
            self.warn = False           #Clear the warn flag immediately
            self.buttonCount += 1
            if self.buttonCount > (DELAY_QUIT / DELAY_MS):
                self.willQuit = True    
            if self.buttonCount > (DELAY_SHUTDOWN / DELAY_MS):
                self.willShutDown = true
            
        #Second, check if we should begin photobooth-ing
        if not self.warn: 
            if self.shouldStartColor():
                self.takePhotos(True)
            elif self.shouldStartBlackWhite():
                self.takePhotos(False)
            
        
        #Finally, schedule ourself to run again
        self.after(Photobooth.DELAY_MS, self.mainBody)
    
    def __init__(self, master):      
        #Setup gpio
        gpio.setmode(gpio.BOARD)
        gpio.setup(Photobooth.BTN_SHUTDOWN, gpio.IN)
        gpio.setup(Photobooth.BTN_PHOTO_CLR, gpio.IN)
        gpio.setup(Photobooth.BTN_PHOTO_BW, gpio.IN)
        #gpio.setup(Photobooth.OUT_LIGHT, gpio.OUT)
        #gpio.setup(Photobooth.OUT_WARNING, gpio.OUT)

        #Initialize PI camera
        self.camera=picamera.PiCamera()
        self.camera.preview_fullscreen = False
        self.camera.resolution = (self.CAMERA_WIDTH, self.CAMERA_HEIGHT)
        self.camera.preview_window = ((self.SCREEN_WIDTH - self.CAMERA_WIDTH) / 2, (self.SCREEN_HEIGHT - self.CAMERA_HEIGHT) / 3, self.CAMERA_WIDTH, self.CAMERA_HEIGHT)

        #Initialize state
        self.printCount = 0
        self.warn = False
        
        #Initialize GUI
        bgImage = PhotoImage(file=self.DIR_IMAGE + "screen_background.png")
        Tkinter.Label.__init__(self, master, image=bgImage)
        self.master = master
        self.image = bgImage
        self.bind("<Escape>", self.closeProgram)
        self.bind("z", self.takePhotos(True))
        self.bind("x", self.takePhotos(False))
        self.pack(side=Tkinter.TOP, expand=Tkinter.YES, fill=Tkinter.BOTH)
        
        #master.overrideredirect(1)
        master.geometry(str(self.SCREEN_WIDTH) + "x" + str(self.SCREEN_HEIGHT) + "+0+0")

        self.focus_set()
    
root = Tkinter.Tk()
root.title("Photobooth")
app = Photobooth(root)
app.after(Photobooth.DELAY_MS, app.mainBody)
app.mainloop()