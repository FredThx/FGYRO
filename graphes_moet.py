#!/usr/bin/python
# -*- coding: utf-8 -*
import sys
sys.path.insert(0,'../FUTIL')

from FGYRO.gyro_ui import *
from FGYRO.gyro_db import *
#Pour travailler sur les sources

from FUTIL.my_logging import *
import datetime
import shutil
import json


my_logging(console_level = DEBUG, logfile_level = DEBUG, details = True)

mybdd = gyro_db(host = 'localhost', topic = 'FILEUROPE/GYRO/1', date_debut = datetime.datetime(2020,7,3,11,00), date_fin = datetime.datetime(2020,7,6,17,59))# datetime.datetime(2017,3,24,23,00))
my_ui = gyro_ui(mybdd)#,'/Users/jimmylefevre/Desktop/remutrack_v2/djim')

my_ui.run()
