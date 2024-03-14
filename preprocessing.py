import numpy as np
from PIL import Image
import argparse
import math
import os
from scipy import misc
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import imageio
import scipy
from skimage.transform import resize
from skimage import color
from skimage import io

databasepath = './build_test'

filelist = os.listdir(databasepath)
total_num = len(filelist)
k = 0
lista = []
for i in range(1, len(filelist)):
    lista.append(str(i)+".png")

backcolor = 0.5
image_size = 128

for name in lista:
    filename = os.path.join(databasepath, name)
    I = color.rgb2gray(imageio.imread(filename))
    I[I == I[0][0]] = backcolor
    crop_img = resize(I, output_shape=(image_size, image_size, 1))
    print(crop_img[0][0])
    imageio.imwrite('./pfp128/%d.png' %(k), crop_img)
    k = k + 1


