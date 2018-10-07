#!/usr/bin/python
# -*- coding: utf-8 -*

#Pour travailler sur les sources
import sys
sys.path.insert(0,'../FUTIL')
from FUTIL.my_logging import *

from pymongo import MongoClient
import matplotlib
import matplotlib.text as matplotlib_text
import matplotlib.pyplot as plt
import matplotlib.cbook as cbook
import matplotlib.dates as matplotlib_dates
from matplotlib.widgets import Button
from matplotlib.patches import Rectangle

#from matplotlib.widgets import TextBox
import datetime
import time
from math import atan2, pi
import os
from datetime import datetime
from FGYRO.gyro_db import *
from FGPIO.f_thread import *
from pathlib import Path

class gyro_ui(object):
	'''Classe pour interface graphique de visualisation des données de remuage
	'''
	def __init__(self, bdd, images_folder = None):
		'''Initialisation
			- bdd			:	base de données gyro_db
		'''
		self.bdd = bdd
		self.dates = []
		self.acc_Xs = []
		self.acc_Ys = []
		self.acc_Zs = []
		self.gyro_Xs = []
		self.gyro_Ys = []
		self.gyro_Zs = []
		self.angle_Xs = []
		self.angle_Ys = []
		self.angle_Zs = []
		self.angle_X = 0
		self.angle_Y = 0
		self.angle_Z = 0
		self.lecture_donnees()
		self.scan_images(images_folder)
		self.fig = plt.figure()
		self.fig.canvas.set_window_title('Fileurope - CMP - FGYRO')
		self.init_graphes()
		self.lecture = False
		self.th_lecture_image = None
		matplotlib.use('GTKAgg') 
		self.vitesse_lecture = 1
		
	def run(self):
		'''Run the ui
		'''
		plt.show()
	
	def lecture_donnees(self):
		'''lecture de la base de données et correction des données
		'''
		logging.info('Lecture des données')
		for data in self.bdd.mesures():
			try:	
				self.dates.append(gyro_db.utc_to_local(data['date']))
				self.acc_Xs.append(data['acc_X'])
				self.acc_Ys.append(data['acc_Y'])
				self.acc_Zs.append(data['acc_Z'])
				self.gyro_Xs.append(data['gyro_X'])
				self.gyro_Ys.append(data['gyro_Y'])
				self.gyro_Zs.append(data['gyro_Z'])
				self.angle_Xs.append(atan2(data['acc_Y'],data['acc_Z']) * 180 / pi)
				self.angle_Ys.append(atan2(data['acc_Z'],data['acc_X']) * 180 / pi)
				self.angle_Zs.append(atan2(data['acc_X'],data['acc_Y']) * 180 / pi)
			except Exception as e:
				print(e)
		logging.info("%s mesures trouvées."%(len(self.dates)))
		
		#Moyenne des vitesses angulaires pour auto-calibration
		try:
			corr_gyro_Xs = sum(self.gyro_Xs)/len(self.gyro_Xs)
		except:
			corr_gyro_Xs = 0
		try:
			corr_gyro_Ys = sum(self.gyro_Ys)/len(self.gyro_Ys)
		except:
			corr_gyro_Ys = 0
		try:
			corr_gyro_Zs = sum(self.gyro_Zs)/len(self.gyro_Zs)
		except:
			corr_gyro_Zs = 0
		logging.info("Correction des moyennes des vitesses angulaires : x:%s, y:%s, z:%s"%(corr_gyro_Xs, corr_gyro_Ys, corr_gyro_Zs))
		
		for i in range(0,len(self.dates)):
			#Correction des vitesses angulaires
			self.gyro_Xs[i] -= corr_gyro_Xs
			self.gyro_Ys[i] -= corr_gyro_Ys
			self.gyro_Zs[i] -= corr_gyro_Zs
			# "Suppression" des mesures d'angle quand il y a une vitesses angulaire
			if i> 0 and (abs(self.gyro_Xs[i]) > 50 or abs(self.gyro_Ys[i]) > 50 or abs(self.gyro_Zs[i]) > 50):
				self.angle_Xs[i] = self.angle_Xs[i-1]
				self.angle_Ys[i] = self.angle_Ys[i-1]
				self.angle_Zs[i] = self.angle_Zs[i-1]
			# Gestion des angles qui passent de pi à -pi
			if abs(self.angle_Xs[i]-self.angle_Xs[i-1])>180:
				if self.angle_Xs[i] < self.angle_Xs[i-1]:
					self.angle_Xs[i] += 360
				else:
					self.angle_Xs[i] -= 360
			if abs(self.angle_Ys[i]-self.angle_Ys[i-1])>180:
				if self.angle_Ys[i] < self.angle_Ys[i-1]:
					self.angle_Ys[i] += 360
				else:
					self.angle_Ys[i] -= 360
			if abs(self.angle_Zs[i]-self.angle_Zs[i-1])>180:
				if self.angle_Zs[i] < self.angle_Zs[i-1]:
					self.angle_Zs[i] += 360
				else:
					self.angle_Zs[i] -= 360

	def init_graphes(self):
		''' Inititialise les graphiques
		'''
		image_capteur = plt.imread('capteur.png')
		self.image_capteur_plot = self.fig.add_subplot(233)
		self.image_capteur_plot.imshow(image_capteur)
		
		self.xyz=self.fig.add_subplot(231)
		#self.xyz.xlabel('Temps')
		#self.xyz.ylabel('x,y,z')
		self.xyz.plot(self.dates, self.acc_Xs, label='acc_X')
		self.xyz.plot(self.dates, self.acc_Ys, label='acc_Y')
		self.xyz.plot(self.dates, self.acc_Zs, label='acc_Z')
		self.xyz.legend() 
		self.xyz_line = False

		self.GxGyGz=self.fig.add_subplot(234, sharex = self.xyz)
		#self.GxGyGz.xlabel('Temps')
		#self.GxGyGz.ylabel('Gx,Gy,Gz')
		self.GxGyGz.plot(self.dates,self.gyro_Xs, label='gyro_X')
		self.GxGyGz.plot(self.dates,self.gyro_Ys, label='gyro_Y')
		self.GxGyGz.plot(self.dates,self.gyro_Zs, label='gyro_Z')
		self.GxGyGz.legend() 
		self.GxGyGz_line = False
			
		self.AxAyAz=self.fig.add_subplot(235, sharex = self.xyz)
		#self.AxAyAz.xlabel('Temps')
		#self.AxAyAz.ylabel('Ax,Ay,Az')
		self.AxAyAz.plot(self.dates,self.angle_Xs, label='angle_X')
		self.AxAyAz.plot(self.dates,self.angle_Ys, label='angle_Y')
		self.AxAyAz.plot(self.dates,self.angle_Zs, label='angle_Z')
		self.AxAyAz.legend() 
		self.AxAyAz_line = False
		
		self.image_plot = self.fig.add_subplot(232)
		
		self.fig.canvas.mpl_connect('button_press_event', self.on_click)
		
		self.bt_lecture = Button(plt.axes([0.65, 0.3, 0.05, 0.03]),'lecture')
		self.bt_lecture.on_clicked(self.on_bt_lecture_click)
		
		self.bt_lecture10 = Button(plt.axes([0.65, 0.2, 0.05, 0.03]),'lecturex10')
		self.bt_lecture10.on_clicked(self.on_bt_lecture_click10)
		#self.tb_vitesse = TextBox(plt.axes([0.9, 0.8, 0.05, 0.03]),'Vitesse', initial = '1')
		#self.tb_vitesse.on_submit(self.on_tb_vitesse_submit)
		
		legende = self.fig.add_axes([0.75,0.1,0.2,0.3])
		legende.set_axis_off()
		#rect = Rectangle((0,0),1,1,fill=True, color= 'blue')
		#legende.add_patch(rect)
		logo_img = plt.imread('logo.png')
		legende.imshow(logo_img)
		text_legende = plt.text(0.05,0.05,u"Remutrace - Brevet déposé.")
		self.fig.canvas.mpl_connect('key_press_event',self.press)
		
		
		
		
	def scan_images(self, rep):
		'''Scan le repertoire des images
			et peuble le dict self.images : {date:nom_fichier _image}
		'''
		logging.info("Scan du repertoir images : %s ..."%(rep))
		self.images = {}
		self.images_dates = {}
		if rep:
			for fichier in  os.listdir(rep):
				if os.path.isfile(os.path.join(rep, fichier)):
					try:
						self.images[datetime.strptime(fichier[3:-4],"%Y-%m-%d %H-%M-%S.%f")]=os.path.join(rep, fichier)
					except:
						pass
			self.images_dates = self.images.keys()
			self.images_dates.sort()
			logging.info("%s images trouvées."%(len(self.images)))
		self.xdate_index = 0

	def show_image(self):
		'''Update the image and the cursors
		'''
		if len(self.images)>0:
			date = self.images_dates[self.xdate_index]
			image_path = self.images[date]
			logging.debug("Image %s"%(image_path))
			image_file = cbook.get_sample_data(image_path)
			image = plt.imread(image_file)
			self.image_plot.clear()
			self.image_plot.imshow(image)
			self.image_plot.text(0, 0, Path(image_path).name)
			if self.xyz_line:
				self.xyz_line.remove()
			self.xyz_line = self.xyz.vlines(date, self.xyz.get_ylim()[0]*0.75, self.xyz.get_ylim()[1]*0.75)
			if self.AxAyAz_line:
				self.AxAyAz_line.remove()
			self.AxAyAz_line = self.AxAyAz.vlines(date, self.AxAyAz.get_ylim()[0]*0.75, self.AxAyAz.get_ylim()[1]*0.75)
			if self.GxGyGz_line:
				self.GxGyGz_line.remove()
			self.GxGyGz_line = self.GxGyGz.vlines(date, self.GxGyGz.get_ylim()[0]*0.75, self.GxGyGz.get_ylim()[1]*0.75)
			self.fig.canvas.draw()	# C'est ici que c'est long (0.3 s)


	def on_click(self, event):
		'''callback function when click on graphe
		'''
		#logging.debug('button=%d, inaxes = %s, x=%d, y=%d, xdata=%f, ydata=%f' %(event.button, event.inaxes, event.x, event.y, event.xdata, event.ydata))
		if len(self.images)>0:
			if event.inaxes in [self.xyz, self.AxAyAz, self.GxGyGz] :
				date = matplotlib_dates.num2date(event.xdata).replace(tzinfo=None)
				try:
					self.xdate_index = self.images_dates.index(min(self.images_dates, key=lambda d: abs(d-date)))
					logging.debug(self.xdate_index)
					self.show_image()
				except:
					pass
	# Attention : bricolage+++	
	def on_bt_lecture_click10(self, event):
		self.vitesse_lecture = 10
		self.on_bt_lecture_click_all(event)
	
	def on_bt_lecture_click(self, event):
		'''
		'''
		self.vitesse_lecture = 1
		self.on_bt_lecture_click_all(event)
	
	def on_bt_lecture_click_all(self, event):
		if self.lecture:
			self.lecture = False
			self.bt_lecture.Label = matplotlib_text.Text(text='lecture')
			logging.info("Pause")
			self.th_lecture_image.stop()
			self.fig.canvas.draw()	
		else:
			self.lecture = True
			self.bt_lecture.Label = matplotlib_text.Text(text='pause')
			logging.info("Lecture")
			self.fig.canvas.draw()	
			self.th_lecture_image = f_thread(self.lecture_images)
			self.th_lecture_image.start()
	# Fin du bricolage
	def lecture_images(self, sens = 1):
		''' affichage de l'image suivante
			Utilisation : en threading  : f_thread(self.lecture_images)
		'''
		self.xdate_index += sens * self.vitesse_lecture
		if self.xdate_index > len(self.images_dates):
			self.xdate_index = 0
			self.lecture = False
		self.show_image()
		time.sleep(0.05) #Pour donner la main à l'affichage
		
	def press(self, event):
		''' Quand une fleche droite ou gauche est appuyée : image suivante ou précédente
		'''
		print("Key pressed : " + event.key)
		sys.stdout.flush()
		if event.key == "down":
			self.lecture_images(1)
		elif event.key == "up":
			self.lecture_images(-1)
		elif event.key == "pagedown":
			self.lecture_images(10)
		elif event.key == "pageup":
			self.lecture_images(-10)
	
	def on_tb_vitesse_submit(self,text):
		''' quand changement vitesse de lecture
		'''
		try:
			self.vitesse_lecture = int(text)
		except:
			pass