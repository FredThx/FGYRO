#!/usr/bin/python
# -*- coding: utf-8 -*

from visual import *
import math
import time
import json


class vgyro(object):
    '''Représentation en vpython de la position du gyro
    '''
    def __init__(self):
        '''Initialisation
        '''
        self.ground = box(pos=(0,0,0), length=40, height=0.1, width=30, color=color.green)
        #self.bottle = arrow(pos=vector(0,5,0), axis=vector(10,1,0), shaftwidth=1)
        self.bottle = box(pos=vector(0,5,0), axis=vector(0,1,0), size = (3 ,1,1))

    def set_acc(self, acc_x, acc_y, acc_z):
        '''Rotate the bottle according with the gravity acceleration (x,y,z)
        '''
        print(acc_x, acc_y, acc_z)
        acc = math.sqrt(acc_x**2 + acc_y**2+ acc_z**2)
        print(acc)
        acc_x = acc_x / acc
        acc_y = acc_y / acc
        acc_z = acc_z / acc
        print(acc_x, acc_y, acc_z)
        # Sur plan x,y
        axis_y = -acc_x
        axis_x = -math.sqrt(1 - acc_x**2)
        print("Set axis : (%f,%f,%s)"%(axis_x, axis_y,0 ))
        print(axis_x**2+axis_y**2)
        axis_z = 0
        print("Set axis : (%f,%f,%f)"%(axis_x, axis_y, axis_z))
        self.bottle.axis =  (axis_x, axis_y, axis_z)
        angle = asin(acc_y/math.sqrt(acc_y**2+acc_z**2))
        print(angle*180/math.pi)
        self.bottle.rotate(angle = angle)


if __name__ == '__main__':
    gyro = vgyro()
    import paho.mqtt.client as mqtt
    client = mqtt.Client("vtest")
    client.connect('10.3.141.1')
    def on_msg(client, data, msg):
        try:
            payload = json.loads(msg.payload)
            #print("x:%f,y:%f,z:%f"%(payload['acc_X'],payload['acc_Y'], payload['acc_Z']))
            gyro.set_acc(payload['acc_X'],payload['acc_Y'], payload['acc_Z'])
        except Exception  as e:
            print(e)

    client.on_message = on_msg
    client.subscribe('FILEUROPE/GYRO/1/datas')
    client.loop_start()
