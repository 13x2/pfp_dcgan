from keras.models import Sequential
from keras.layers import Dense, Dropout, LeakyReLU
from keras.layers import Reshape
from keras.layers.core import Activation
from keras.layers.normalization import BatchNormalization
from keras.layers.convolutional import UpSampling2D
from keras.layers.convolutional import Conv2D, MaxPooling2D
from keras.layers.core import Flatten
from keras.optimizers import SGD, Adam
from skimage import color
#from keras.datasets import mnist
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

os.environ["CUDA_VISIBLE_DEVICES"]="0"

def generator_model():
    model = Sequential()

    model.add(Dense(input_dim=100, output_dim = 16*16*512))
    model.add(BatchNormalization(momentum=0.9))
    model.add(Activation('relu'))
    model.add(Reshape((16, 16, 512)))

    model.add(Conv2D(256, (3, 3), padding='same'))
    model.add(BatchNormalization(momentum=0.9))
    model.add(Activation('relu'))
    model.add(UpSampling2D(size=(2, 2)))

    model.add(Conv2D(128, (3, 3), padding='same'))
    model.add(BatchNormalization(momentum=0.9))
    model.add(Activation('relu'))
    model.add(UpSampling2D(size=(2, 2)))

    model.add(Conv2D(64, (3, 3), padding='same'))
    model.add(BatchNormalization(momentum=0.9))
    model.add(Activation('relu'))
    model.add(UpSampling2D(size=(2, 2)))

    model.add(Conv2D(32, (3, 3), padding='same'))
    model.add(BatchNormalization(momentum=0.9))
    model.add(Activation('relu'))
    model.add(UpSampling2D(size=(1, 1)))

    model.add(Conv2D(1, (3, 3), padding='same'))
    model.add(Activation('tanh'))
    return model


def discriminator_model():
    Drop = 0.5

    model = Sequential()
    model.add(
            Conv2D(64, (3, 3),
            padding='same',
            input_shape=(128, 128, 1))
            )
    model.add(LeakyReLU(alpha=0.2))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    #model.add(Dropout(Drop))

    model.add(Conv2D(128, (3, 3)))
    model.add(LeakyReLU(alpha=0.2))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    #model.add(Dropout(Drop))

    model.add(Conv2D(256, (3, 3)))
    model.add(LeakyReLU(alpha=0.2))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    #model.add(Dropout(Drop))

    model.add(Conv2D(512, (3, 3)))
    model.add(LeakyReLU(alpha=0.2))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    #model.add(Dropout(Drop))

    '''    model.add(Conv2D(1024, (3, 3)))
    model.add(LeakyReLU(alpha=0.2))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    #model.add(Dropout(Drop))'''

    model.add(Flatten())
    model.add(Dense(1))
    model.add(Activation('sigmoid'))
    return model


def generator_containing_discriminator(g, d):
    model = Sequential()
    model.add(g)
    d.trainable = False
    model.add(d)
    return model


def combine_images(generated_images):
    num = generated_images.shape[0]
    width = int(math.sqrt(num))
    height = int(math.ceil(float(num)/width))
    shape = generated_images.shape[1:3]
    image = np.zeros((height*shape[0], width*shape[1]),
                     dtype=generated_images.dtype)
    for index, img in enumerate(generated_images):
        i = int(index/width)
        j = index % width
        image[i*shape[0]:(i+1)*shape[0], j*shape[1]:(j+1)*shape[1]] = \
            img[:, :, 0]
    return image

def splite_dataset(ratio = 1):
    databasepath = '.\sdpfp128'
    filelist = os.listdir(databasepath)
    X_train = np.zeros([int(len(filelist) * ratio), 128, 128])
    X_test = np.zeros([int(len(filelist) * (1-ratio)), 128, 128])
    y_train = np.zeros([int(len(filelist) * ratio)])
    y_test = np.zeros([int(len(filelist) * (1-ratio))])
    for (name, i) in zip(filelist, range(0, len(filelist))):
        filename = os.path.join(databasepath, name)
        X_train[i, :, :] = imageio.imread(filename)
    return X_train, y_train, X_test, y_test

def train(X_train, y_train, X_test, y_test, BATCH_SIZE, EPOCHS):
    saveweightpath = "./train/weight/"
    predimagepath = "./train/img0730/"
    if not os.path.exists(predimagepath):
        os.makedirs(predimagepath)
    X_train = (X_train.astype(np.float32) - 127.5)/127.5
    X_train = X_train[:, :, :, None]
    X_test = X_test[:, :, :, None]
    # X_train = X_train.reshape((X_train.shape, 1) + X_train.shape[1:])
    d = discriminator_model()
    g = generator_model()
    d_on_g = generator_containing_discriminator(g, d)
    # d_optim = SGD(lr=0.0005, momentum=0.9, nesterov=True)
    # g_optim = SGD(lr=0.0005, momentum=0.9, nesterov=True)
    d_optim = Adam(lr=0.0001, beta_1=0.5, decay=1e-8)
    g_optim = Adam(lr=0.0001, beta_1=0.5, decay=1e-8)
    g.compile(loss='binary_crossentropy', optimizer="Adam")
    d_on_g.compile(loss='binary_crossentropy', optimizer=g_optim)
    d.trainable = True
    d.compile(loss='binary_crossentropy', optimizer=d_optim)
    d_loss_list = []
    g_loss_list = []
    for epoch in range(EPOCHS):
        print("Epoch is", epoch)
        print("Number of batches", int(X_train.shape[0]/BATCH_SIZE))
        for index in range(int(X_train.shape[0]/BATCH_SIZE)):
            noise = np.random.uniform(-1, 1, size=(BATCH_SIZE, 100))
            image_batch = X_train[index*BATCH_SIZE:(index+1)*BATCH_SIZE]
            generated_images = g.predict(noise, verbose=0)
            if index % 50 == 0:
                image = combine_images(generated_images)
                image = image*127.5+127.5
                Image.fromarray(image.astype(np.uint8)).save(
                    predimagepath+str(epoch)+"_"+str(index)+".png")
            X = np.concatenate((image_batch, generated_images))
            y = [1] * BATCH_SIZE + [0] * BATCH_SIZE
            d_loss = d.train_on_batch(X, y)
            d_loss_list.append([d_loss])
            print("batch %d d_loss : %f" % (index, d_loss))
            noise = np.random.uniform(-1, 1, (BATCH_SIZE, 100))
            d.trainable = False
            g_loss = d_on_g.train_on_batch(noise, [1] * BATCH_SIZE)
            d.trainable = True
            print("batch %d g_loss : %f" % (index, g_loss))
            g_loss_list.append([g_loss])
#            if index == int(X_train.shape[0]/BATCH_SIZE)-1:
#                g.save_weights(saveweightpath+str(epoch)+"_"+str(index)+'generator', True)
#                d.save_weights(saveweightpath+str(epoch)+"_"+str(index)+'discriminator', True)


def generate(BATCH_SIZE, nice=False):
    loadpath = ""
    g = generator_model()
    g.compile(loss='binary_crossentropy', optimizer="Adam")
    g.load_weights('generator')
    if nice:
        d = discriminator_model()
        d.compile(loss='binary_crossentropy', optimizer="Adam")
        d.load_weights('discriminator')
        noise = np.random.uniform(-1, 1, (BATCH_SIZE*20, 100))
        generated_images = g.predict(noise, verbose=1)
        d_pret = d.predict(generated_images, verbose=1)
        index = np.arange(0, BATCH_SIZE*20)
        index.resize((BATCH_SIZE*20, 1))
        pre_with_index = list(np.append(d_pret, index, axis=1))
        pre_with_index.sort(key=lambda x: x[0], reverse=True)
        nice_images = np.zeros((BATCH_SIZE,) + generated_images.shape[1:3], dtype=np.float32)
        nice_images = nice_images[:, :, :, :]
        for i in range(BATCH_SIZE):
            idx = int(pre_with_index[i][1])
            nice_images[i, :, :, :] = generated_images[idx, :, :, :]
        image = combine_images(nice_images)
    else:
        noise = np.random.uniform(-1, 1, (BATCH_SIZE, 100))
        generated_images = g.predict(noise, verbose=1)
        image = combine_images(generated_images)
    image = image*127.5+127.5
    Image.fromarray(image.astype(np.uint8)).save(
        "generated_image.png")


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str)
    parser.add_argument("--batch_size", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--nice", dest="nice", action="store_true")
    parser.set_defaults(nice=False)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = get_args()
    if args.mode == "train":
        X_train, y_train, X_test, y_test = splite_dataset(ratio=1)
        train(X_train, y_train, X_test, y_test, BATCH_SIZE=args.batch_size, EPOCHS = args.epochs)
    elif args.mode == "generate":
        generate(BATCH_SIZE=args.batch_size, nice=args.nice)
