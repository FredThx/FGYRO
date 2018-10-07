#!/usr/bin/python
# -*- coding: utf-8 -*

#Pour travailler sur les sources
import sys
sys.path.insert(0,'../FUTIL')
from FUTIL.my_logging import *

from pymongo import MongoClient
import calendar
from datetime import datetime, timedelta
import pytz


class gyro_db(object):
	'''A database Mongodb pour stocker données capteur gyro
	'''
	def __init__(self, connect_string = None, host = '127.0.0.1', port = 27017, db_name = 'fileurope', date_debut = None, date_fin = None, TIMEZONE = 'Europe/Paris'):
		'''Initialisation
			- host				:	mongodb host (default : localhost)
			- port				:	mongodb port (default : 27017)
			- db_name			;	database name (default : 'fileurope')
			- date_debut
			- date_fin
		'''
		if connect_string:
			self.client = MongoClient(connect_string)
		else:
			self.client = MongoClient(host, port)
		self.db = self.client[db_name]
		self.datas = self.db.gyro
		self.tz = pytz.timezone(TIMEZONE)
		self.date_debut = self.tz.localize(date_debut)
		self.date_fin = self.tz.localize(date_fin)
		
	
	def mesures(self):
		'''renvoie un iterable avec les mesures
		'''
		#TODO : ajouter des critères (batch, ...)
		criteres = {}
		if self.date_debut or self.date_fin:
			criteres['date']={}
		if self.date_debut:
			criteres['date']['$gte']=self.date_debut
		if self.date_fin:
			criteres['date']['$lte']=self.date_fin
		return self.datas.find(criteres).sort('date')
	
	@staticmethod
	def utc_to_local(utc_dt):
		''' Transforme une date UTC en date locale naive
		'''
		timestamp = calendar.timegm(utc_dt.timetuple())
		local_dt = datetime.fromtimestamp(timestamp)
		assert utc_dt.resolution >= timedelta(microseconds=1)
		return local_dt.replace(microsecond=utc_dt.microsecond)