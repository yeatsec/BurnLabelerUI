import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
import imageio as io
import os, sys

class BurnLabelerUI(object):

    paths = ["labeled/burned/", "labeled/burned/first/", "labeled/burned/second/", "labeled/burned/third/", "labeled/burned/all/", "labeled/healthy/", "labeled/background/", "labeled/originals/"]
    labelspec = False
    colors = [None, 'pink', 'magenta', 'r', 'b']

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
        self.fig.canvas.set_window_title(self.imname)
        plt.subplots_adjust(bottom=0.2)
        self.imax = self.ax.imshow(self.im)
        # following could be done more elegantly with lists but w/e
        # set up Buttons
        healthybutt = plt.axes([0.5, 0.05, 0.09, 0.075])
        backgroundbutt = plt.axes([0.6, 0.05, 0.09, 0.075])
        undobutt = plt.axes([0.7, 0.05, 0.09, 0.075])
        donebutt = plt.axes([0.8, 0.05, 0.09, 0.075])
        specificbutt = plt.axes([0.1, 0.05, 0.09, 0.075])
        firstbutt = plt.axes([0.2, 0.05, 0.09, 0.075])
        secondbutt = plt.axes([0.3, 0.05, 0.09, 0.075])
        thirdbutt = plt.axes([0.4, 0.05, 0.09, 0.075])
        
        bhealthy = Button(healthybutt, 'Healthy', color='b', hovercolor='w')
        bhealthy.on_clicked(self.healthyCursor)
        bundo = Button(undobutt, 'Undo')
        bundo.on_clicked(self.undo)
        bbackground = Button(backgroundbutt, 'Background')
        bbackground.on_clicked(self.backgroundCursor)
        bdone = Button(donebutt, 'Done')
        bdone.on_clicked(self.done)
        bspecific = Button(specificbutt, 'Toggle 123', color='g')
        bspecific.on_clicked(self.specificToggle)
        bfirst = Button(firstbutt, 'First', color=self.colors[1])
        bfirst.on_clicked(self.firstCursor)
        bsecond = Button(secondbutt, 'Second', color=self.colors[2])
        bsecond.on_clicked(self.secondCursor)
        bthird = Button(thirdbutt, 'Third', color=self.colors[3])
        bthird.on_clicked(self.thirdCursor)
        # declare artist data
        self.rects = list()
        # set up onClick
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidmo = self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cidor = self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.isClosing = False
        # data structures for undo
        self.staged = list()
        self.history = list()
        
        plt.show()


    def inBounds(self, y, x):
        return (y >= 0.0 and y < self.imageMatrix.shape[0]*self.side and x >= 0.0 and x < self.imageMatrix.shape[1]*self.side)

    def done(self, event):
        self.isClosing = True
        # disconnect clicky
        self.fig.canvas.mpl_disconnect(self.cid)
        self.fig.canvas.mpl_disconnect(self.cidmo)
        self.fig.canvas.mpl_disconnect(self.cidor)
        # save subimages and close (perhaps move image to a 'classified' folder)
        for row in range(self.imageMatrix.shape[0]):
            for col in range(self.imageMatrix.shape[1]):
                cellval = self.imageMatrix[row][col]
                assert (cellval >= -1 and cellval <= 3), "corrupt data of {} at row {} col {}".format(cellval, row, col)
                subim = self.im[row*self.side:row*self.side+self.side, col*self.side:col*self.side+self.side, :]
                name = self.imname + '_size' + str(self.side) + '_row' + str(row*self.side) + '_col' + str(col*self.side)
                if (cellval == -1): # Healthy
                    io.imwrite('./labeled/healthy/'+name+'.bmp', subim)
                elif (self.imageMatrix[row][col] == 0): # Background
                    io.imwrite('./labeled/background/'+name+'.bmp', subim)
                else:
                    if self.labelspec:
                        io.imwrite(self.paths[cellval]+name+'.bmp', subim) # if labeling specifically, write to specific location
                    io.imwrite('./labeled/burned/all/'+name+'.bmp', subim) # always save generic 'burned' photos
        plt.close()

    def undo(self, event):
        # if exists, restore previous state
        if len(self.history):
            self.imageMatrix = self.history.pop()
        self.annotate()

    def firstCursor(self, event):
        self.cursor = 1

    def secondCursor(self, event):
        self.cursor = 2

    def thirdCursor(self, event):
        self.cursor = 3

    def healthyCursor(self, event):
        self.cursor = -1

    def backgroundCursor(self, event):
        self.cursor = 0

    def specificToggle(self, event):
        self.labelspec = not self.labelspec

    def annotate(self):
        self.ax.set_title("1st 2nd 3rd Burn Labeling" if self.labelspec else "Nonspecific Burn Labeling")
        for rect in self.rects:
            rect.remove()
        self.rects = list()
        for row in range(self.imageMatrix.shape[0]):
            for col in range(self.imageMatrix.shape[1]):
                cellval = self.imageMatrix[row][col]
                assert (cellval >= -1 and cellval <= 3), "corrupt data of {} at row {} col {}".format(cellval, row, col)
                if cellval != 0:
                    self.rects.append(Rectangle((col*self.side, row*self.side), self.side, self.side, fc=self.colors[cellval], alpha=0.3))
        for rect in self.rects:
            self.ax.add_patch(rect)
        self.fig.canvas.draw()

    def on_press(self, event):
        self.held_down = True
        if event.inaxes != self.imax.axes: return
        # determine where the click happened
        try:
            # stage changes for data structure
            if self.inBounds(event.ydata, event.xdata): # hack to prevent button clicking from messing with the data structure
            	self.staged.append((int(event.ydata/self.side), int(event.xdata/self.side), self.cursor))
        except TypeError:
            print("Clicked Off Picture")
        except IndexError:
        	print("Pixels beyond grid structure; This region will not be saved as either burned, healthy, or background.")

    def on_motion(self, event):
        if event.inaxes != self.imax.axes: return
        try:
            if (self.held_down and self.inBounds(event.ydata, event.xdata)): # hack to prevent button clicking from messing with the data structure
                self.staged.append((int(event.ydata/self.side), int(event.xdata/self.side), self.cursor))
        except:
            print("Drag attempted")

    def on_release(self, event):
        self.held_down = False
        # save former data structure
        if len(self.staged):
            self.history.append(self.imageMatrix.copy())
        # commit changes
        while len(self.staged):
            row, col, cur = self.staged.pop()
            self.imageMatrix[row][col] = cur
        if not self.isClosing:
            self.annotate()

blui = BurnLabelerUI('unlabeled/burn.jpg', 50)