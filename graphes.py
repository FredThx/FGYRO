#!/usr/bin/python
# -*- coding: utf-8 -*

from FGYRO.gyro_ui import *
from FGYRO.gyro_db import *
#Pour travailler sur les sources
import sys
sys.path.insert(0,'../FUTIL')
from FUTIL.my_logging import *
import datetime


my_logging(console_level = DEBUG, logfile_level = DEBUG, details = True)

#atlas_connect_string = "mongodb://fthome:Vosges_88@clustergyro-shard-00-00-xwf7y.mongodb.net:27017,clustergyro-shard-00-01-xwf7y.mongodb.net:27017,clustergyro-shard-00-02-xwf7y.mongodb.net:27017/?ssl=true&replicaSet=ClusterGYRO-shard-0&authSource=admin"
#mybdd = gyro_db(host = '192.168.7.17')
mybdd = gyro_db(host = 'localhost', topic = 'FILEUROPE/GYRO/1', date_debut = datetime.datetime(2018,7,13,15,00), date_fin = datetime.datetime(2018,7,17,15,00))# datetime.datetime(2017,3,24,23,00))
#mybdd = gyro_db(connect_string = atlas_connect_string)
my_ui = gyro_ui(mybdd,'c:\\fileurope\\FGYRO\\capture')
my_ui.run()
