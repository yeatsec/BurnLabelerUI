import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
import imageio as io
import os, sys

class BurnLabelerUI(object):

    paths = ["labeled/burned/", "labeled/healthy/", "labeled/background/", "labeled/originals/"]
    
    def __init__(self, image_path, dim):
        # ensure that directories are set up
        if not (os.path.exists("labeled") and os.path.isdir("labeled")):
            print("attempting to create labeled directory")
            try:
                os.mkdir("labeled")
            except OSError:
                print("failed to create labeled directory")
            else:
                print("successfully created labeled directory")

        for path in self.paths:
            if not (os.path.exists(path) and os.path.isdir(path)):
                print("attempting to create %s" % path)
                try:
                    os.mkdir(path)
                except OSError:
                    print("Failed to create %s" % path)
                else:
                    print("successfully created %s" % path)

        self.im = io.imread(image_path)
        self.imname = image_path
        # remove any directory specification
        if (self.imname.rfind('/')):
        	self.imname = self.imname[self.imname.rfind('/')+1:]
        if (self.imname.rfind('\\')): # windows
        	self.imname = self.imname[self.imname.rfind('\\')+1:]
        self.side = dim
        self.imshape = self.im.shape
        self.imageMatrix = np.zeros((int(self.imshape[0]/dim), int(self.imshape[1]/dim)), dtype=int)
        self.cursor = 0
        self.held_down = False # state for the on_motion function
        # get fig, ax, display the image
        self.fig, self.ax = plt.subplots()
        plt.subplots_adjust(bottom=0.2)
        plt.imshow(self.im)
        # set up Buttons
        burnedbutt = plt.axes([0.5, 0.05, 0.09, 0.075])
        healthybutt = plt.axes([0.6, 0.05, 0.09, 0.075])
        backgroundbutt = plt.axes([0.7, 0.05, 0.09, 0.075])
        donebutt = plt.axes([0.8, 0.05, 0.09, 0.075])
        startoverbutt = plt.axes([0.1, 0.05, 0.09, 0.075])
        bburned = Button(burnedbutt, 'Burned', color='r', hovercolor='w')
        bburned.on_clicked(self.burnedCursor)
        bhealthy = Button(healthybutt, 'Healthy', color='b', hovercolor='w')
        bhealthy.on_clicked(self.healthyCursor)
        bbackground = Button(backgroundbutt, 'Background')
        bbackground.on_clicked(self.backgroundCursor)
        bdone = Button(donebutt, 'Done')
        bstartover = Button(startoverbutt, 'Start Over')
        bstartover.on_clicked(self.startOver)
        bdone.on_clicked(self.done)
        # declare artists
        self.burnedRects = list()
        self.healthyRects = list()
        # set up onClick
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidmo = self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cidor = self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        
        plt.show()

    def done(self, event):
        # disconnect clicky
        self.fig.canvas.mpl_disconnect(self.cid)
        self.fig.canvas.mpl_disconnect(self.cidmo)
        self.fig.canvas.mpl_disconnect(self.cidor)
        # save subimages and close (perhaps move image to a 'classified' folder)
        for row in range(self.imageMatrix.shape[0]):
            for col in range(self.imageMatrix.shape[1]):
                subim = self.im[row*self.side:row*self.side+self.side, col*self.side:col*self.side+self.side, :]
                name = self.imname + '_size' + str(self.side) + '_row' + str(row*self.side) + '_col' + str(col*self.side)
                if (self.imageMatrix[row][col] == -1): # Healthy
                    io.imwrite('./labeled/healthy/'+name+'.bmp', subim)
                elif (self.imageMatrix[row][col] == 1): # Burned
                    io.imwrite('./labeled/burned/'+name+'.bmp', subim)
                elif (self.imageMatrix[row][col] == 0): # Background
                    io.imwrite('./labeled/background/'+name+'.bmp', subim)
                else:
                    raise ValueError('Invalid subimage label type: ' + str(self.imageMatrix[row][col]) + ' at '+str(row) + ' ' + str(col))
        plt.close()

    def burnedCursor(self, event):
        self.cursor = 1

    def healthyCursor(self, event):
        self.cursor = -1

    def backgroundCursor(self, event):
        self.cursor = 0

    def startOver(self, event):
        self.imageMatrix = np.zeros(self.imageMatrix.shape, dtype=int)
        self.annotate()

    def annotate(self):
        for rect in self.healthyRects:
            rect.remove()
        for rect in self.burnedRects:
            rect.remove()
        self.healthyRects = list()
        self.burnedRects = list()
        for row in range(self.imageMatrix.shape[0]):
            for col in range(self.imageMatrix.shape[1]):
                if (self.imageMatrix[row][col] == -1):
                    self.healthyRects.append(Rectangle((col*self.side, row*self.side), self.side, self.side, fc='b', alpha=0.3))
                elif (self.imageMatrix[row][col] == 1):
                    self.burnedRects.append(Rectangle((col*self.side, row*self.side), self.side, self.side, fc='r', alpha=0.3))
        for rect in self.healthyRects:
            self.ax.add_patch(rect)
        for rect in self.burnedRects:
            self.ax.add_patch(rect)
        self.fig.canvas.draw()
        print("annotate")


    def on_press(self, event):
        self.held_down = True
        # determine where the click happened
        try:
            print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' % 
            ('double' if event.dblclick else 'single', event.button, event.x, event.y, event.xdata, event.ydata))
            # adjust data structure
            if (event.ydata > 1.0):
            	self.imageMatrix[int(event.ydata/self.side)][int(event.xdata/self.side)] = self.cursor
        except TypeError:
            print("Clicked Off Picture")
        except IndexError:
        	print("Pixels beyond grid structure; This region will not be saved as either burned, healthy, or background.")

    def on_motion(self, event):
        try:
            if (self.held_down and event.ydata > 1.0):
                self.imageMatrix[int(event.ydata/self.side)][int(event.xdata/self.side)] = self.cursor
        except:
            print("Drag attempted")

    def on_release(self, event):
        self.held_down = False
        self.annotate()
        

blui = BurnLabelerUI('unlabeled/burn.jpg', 50)