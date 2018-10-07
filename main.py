#!/usr/bin/env python
# -*- coding:utf-8 -*

from FUTIL.my_logging import *
from FGYRO.mqtt_camera import *
from FGPIO.rpiduino_io import *
from FGPIO.led_io import *

my_logging(console_level = DEBUG, logfile_level = DEBUG, details = False)
logging.info('FGYRO.main.py start')

pc = rpiduino_io()
leds = led_io(pc.bcm_pin(23))


cam = mqtt_camera(image_folder = './capture/', mqtt_base_topic = 'FILEUROPE/CAM', leds = leds)
cam.loop_forever()
