#! /usr/bin/env python

'''
Script to automate selection of burn images for labeling
'''

from labeler import BurnLabelerUI
import os
import sys

path = os.getcwd() + "/unlabeled/"
dim = 50

if (len(sys.argv) > 1):
    path = sys.argv[1]
    print("using dir")
else:
    print("using default path: " + path)

contents = list(map(lambda x: os.path.join(path, x), os.listdir(path)))
print(contents)
image_names = list(filter(lambda x: not os.path.isdir(x), contents))
print(image_names)

for imname in image_names:
    blui = BurnLabelerUI(imname, dim)

