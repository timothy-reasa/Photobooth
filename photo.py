# Raspberry Pi PhotoBooth by Bret Lanuis
# Modified by Tim Reasa (timothy.reasa@gmail.com)
# Using Pi Camera Module
# Requires PIL and picamera libraries
# http://github.com/waveform80/picamera
# Pythonware.com/products/pil

import PIL.Image
import ImageDraw
import os, sys
import picamera
import time
import Tkinter as tk
import RPi.gpio as gpio

#Declare constants
BTN_SHUTDOWN = 4
BTN_PHOTO = 22
OUT_LIGHT = 17
#OUT_WARNING =
DELAY_MS = 100
MAX_PRINTS = 25
DIR_SAVE = "/home/pi/photobooth/captured images/"	#for individual camera snapshots
DIR_COMPOSITE = "/home/pi/photobooth/final images/" #for final composite images for printing
DIR_IMAGE = "/home/pi/photobooth/base images/"		#for static background images
TEST = True #True no printout and shutdown only warns

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
root.geometry("660x440+0+0")

pane1 = tk.Frame(root, relief=RAISED, borderwidth=2)
pane1.pack(side=TOP, expand=YES, fill=BOTH)    

bgImage = tk.PhotoImage(file=DIR_IMAGE + "screen background.gif")
bg = tk.Label(pane1, image=bgImage)
bg.image = bgImage
#bg.place(x=0, y=0, relwidth=1, relheight=1)
bg.pack()
btn1 =tk.Button(pane1, text="quit", command=btn_click)
btn1.place(x=0, y=0)
#btn1.pack()

#Initialize PI camera
camera=picamera.PiCamera()
camera.preview_fullscreen = False
camera.preview_window = (290, 100, 350, 350)
#camera.color_effects = (128, 128)
camera.resolution = (350, 350)
#camera.crop = (0.5, 0.5, 1.0, 1.0)

#Initialize state
printCount = 0
off = False
shutter = False

#Main loop
root.after(DELAY_MS, checkButton)
root.mainloop()

def btn_click():
    gpio.cleanup()
    sys.exit(0)

def checkButton():
    #checkShutdown()
        
    if gpio.input(BTN_PHOTO):
	    takePhotos()
		
    root.after(DELAY_MS, checkButton)

def checkShutdown():
    off = gpio.input(BTN_SHUTDOWN)
    if off:
        if TEST:
            os.system("sudo shutdown -k now shutdown button pressed [testing]")
        else:
            os.system("sudo shutdown -h now shutdown button pressed")
            sys.exit(0)
        
def doPhotoPrint(filename):
    if TEST:
        os.system("lp " + filename)
        global printCount
        printCount += 1

def lightOn():
    gpio.output(OUT_LIGHT, 1)

def lightOff():
    gpio.output(OUT_LIGHT, 0)
	
def takeSinglePhoto(filename):
    lightOn()
    camera.hflip = True
    camera.start_preview()
    time.sleep(5)
    camera.hflip = False
    camera.capture(filename)
    camera.stop_preview()
    lightOff()
         
def takePhotos():
    #Start taking Photos
    today = time.strftime("%d-%m-%Y")
    path = DIR_SAVE + today + "/"
    print os.path.isdir(path)
    if not (os.path.isdir(path)):
        os.mkdir(path)
    
    now = time.strftime("%H%M%S")
	
    takeSinglePhoto(path + now + "A.jpg")
    time.sleep(0.5)
    takeSinglePhoto(path + now + "B.jpg")
    time.sleep(0.5)
    takeSinglePhoto(path + now + "C.jpg")
    time.sleep(0.5)
    takeSinglePhoto(path + now + "D.jpg")

    try:
        imagename1 = path + now + "A.jpg"
        im1 = PIL.Image.open(path + now + "A.jpg")
        im2 = PIL.Image.open(path + now + "B.jpg")
        im3 = PIL.Image.open(path + now + "C.jpg")
        im4 = PIL.Image.open(path + now + "D.jpg")
    except:
        print sys.exc_value
        print "Unable to load Images"
        print (imagename1)
        exit(1)
    print "Images loaded"

    try:
        final = PIL.Image.open(DIR_IMAGE + "print background.png")
    except:
        print "Unable to load BG"
        exit(1)

    final.paste(im1, (30,180))
    final.paste(im2, (420,180))
    final.paste(im3, (30,570))
    final.paste(im4, (420,570))
    
    final.save(DIR_COMPOSITE + now + ".png")

    doPhotoPrint(DIR_COMPOSITE + now + ".png")