#!/usr/bin/python
# -*- coding: utf-8 -*

#TODOs
# Peux-être rajouter infos détail étape
# Revoir axes dates pas lisible


#Pour travailler sur les sources
import sys
sys.path.insert(0,'../FUTIL')
from FUTIL.my_logging import *

from pymongo import MongoClient
import matplotlib
import matplotlib.text as matplotlib_text
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cbook as cbook
from matplotlib.widgets import Button
from matplotlib.patches import Rectangle
import matplotlib.ticker as ticker

#from matplotlib.widgets import TextBox
import datetime
import time
from math import atan2, pi, sqrt, acos, asin, sin
import os
from FGYRO.gyro_db import *
from FGPIO.f_thread import *
#from FGYRO.gyro_3D import *
from pathlib import Path

#Pour supprimer les messages de matplotlib
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)

class gyro_ui(object):
	'''Classe pour interface graphique de visualisation des données de remuage
	'''
	format_date = "%d %b %Y %H:%M:%S"
	date_formatter =  mdates.DateFormatter("%d %b") # For axis
	#date_formatter =  ticker.FormatStrFormatter('%d %b') # for axis
	ratio_gyro = 131.0 #Gyro : 1/131 degrés/secondes
	ratio_acceleration = 16384.0 #Acceleration : 1/16384 g (g=9.81 N.s-2)
	seuil_gyro_mvt = 200.0 / 131.0 #Seuil au delà duquel une vitesse angulaire est considéré comme un mvt
	accel_detect = 1000.0 / 131.0
	trig_detect = datetime.timedelta(minutes=10)
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
		#self.angle_Zs = []
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
		self.vitesse_lecture = 1

	def run(self):
		'''Run the ui
		'''
		plt.show()

	def lecture_donnees(self):
		'''lecture de la base de données et correction des données
		'''
		logging.info('Lecture des donnees')
		for data in self.bdd.mesures():
			try:
				self.dates.append(gyro_db.utc_to_local(data['date']))
				self.acc_Xs.append(data['acc_X']/gyro_ui.ratio_acceleration)
				self.acc_Ys.append(data['acc_Y']/gyro_ui.ratio_acceleration)
				self.acc_Zs.append(data['acc_Z']/gyro_ui.ratio_acceleration)
				self.gyro_Xs.append(data['gyro_X']/gyro_ui.ratio_gyro)
				self.gyro_Ys.append(data['gyro_Y']/gyro_ui.ratio_gyro)
				self.gyro_Zs.append(data['gyro_Z']/gyro_ui.ratio_gyro)

				###Calculs angulaires

				# Accélération totale : c'est la pesanteur
				acc = sqrt(data['acc_X']**2 + data['acc_Y']**2 + data['acc_Z']**2)
				#Rotation autour de l'axe de la bouteille (c'est le roulis)
				self.angle_Xs.append(asin(data['acc_Z']/acc) * 180 / pi)
				#Inclinaison de la bouteille vers le bas (c'est le tanguage)
				self.angle_Ys.append(acos(data['acc_X']/acc) * 180 / pi)
				#self.angle_Zs.append(0)
			except Exception as e:
				print(e)

		logging.info("%s mesures trouvees."%(len(self.dates)))

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
		nb_supp_mesures_angle = 0
		for i in range(len(self.dates)):
			#Correction des vitesses angulaires
			self.gyro_Xs[i] -= corr_gyro_Xs
			self.gyro_Ys[i] -= corr_gyro_Ys
			self.gyro_Zs[i] -= corr_gyro_Zs
			# "Suppression" des mesures d'angle quand il y a une vitesses angulaire
			if i> 0 and (abs(self.gyro_Xs[i]) > gyro_ui.seuil_gyro_mvt or abs(self.gyro_Ys[i]) > gyro_ui.seuil_gyro_mvt or abs(self.gyro_Zs[i]) > gyro_ui.seuil_gyro_mvt):
				self.angle_Xs[i] = self.angle_Xs[i-1]
				self.angle_Ys[i] = self.angle_Ys[i-1]
				#self.angle_Zs[i] = self.angle_Zs[i-1]
				nb_supp_mesures_angle += 1
		logging.info("%s mesures d'angle supprimees"%nb_supp_mesures_angle)

		# Recherche des phases
		self.phases = [] # Un enregistrement par phase
		self.etapes = [] # A chaque point, la phase correspondante
		i = 0
		while i<len(self.dates):
			acceleration = sqrt(self.gyro_Xs[i]**2+self.gyro_Ys[i]**2+self.gyro_Zs[i]**2)
			if acceleration > gyro_ui.accel_detect:
				acceleration_max = acceleration
				date_debut_mouvement = self.dates[i]
				date_fin_mouvement = date_debut_mouvement
				date_fin_trig = date_debut_mouvement + gyro_ui.trig_detect
				while self.dates[i] < date_fin_trig:
					acceleration = sqrt(self.gyro_Xs[i]**2+self.gyro_Ys[i]**2+self.gyro_Zs[i]**2)
					acceleration_max = max(acceleration_max, acceleration)
					if acceleration > gyro_ui.accel_detect:
						date_fin_phase = self.dates[i]
					i+=1
				self.phases.append({'debut_mvt' : date_debut_mouvement, 'fin_mvt' : date_fin_mouvement, 'acceleration_max' : acceleration_max})
				logging.info("Phase detectee : no %s : debut = %s, fin = %s"%(len(self.phases),date_debut_mouvement,date_fin_mouvement))
			else:
				i+=1
			self.etapes.append(len(self.phases))
		self.export_xls()

	def export_xls(self, filename = None):
		'''Exporte les données vers un fichier excel
		'''
		#TODO mettre menu dans interface
		if filename is None:
			filename = "gyro.xlsx"
		import xlsxwriter
		workbook = xlsxwriter.Workbook(filename)
		worksheet = workbook.add_worksheet("phases")
		format_date = workbook.add_format({'num_format': 'dd/mm/yy hh:mm:ss'})
		col = 0
		for key in self.phases[0]:
			row = 0
			worksheet.write(row, col, key)
			row +=1
			for item in self.phases:
				if "date" in key:
					worksheet.write_datetime(row, col, self.phases[row-1][key],format_date)
				else:
					worksheet.write(row, col, self.phases[row-1][key])
				row+=1
			col+=1
		workbook.close()


	def init_graphes(self):
		''' Inititialise les graphiques
		'''
		### IMAGE REMUTRACE
		image_capteur = plt.imread('capteur.png')
		self.image_capteur_plot = self.fig.add_subplot(233)
		self.image_capteur_plot.set_axis_off()
		self.image_capteur_plot.imshow(image_capteur)

		### 3D (non implementé)
		#self.3D = figure3D().add_subplot(233)
		#self.3D = self.fig.add_subplot(233)

		### GRAPHE XYZ
		#self.xyz=self.fig.add_subplot(231)
		#self.xyz.set_xlabel('Temps')
		#self.xyz.set_ylabel('x,y,z')
		#self.xyz.plot(self.dates, self.acc_Xs, label='acc_X')
		#self.xyz.plot(self.dates, self.acc_Ys, label='acc_Y')
		#self.xyz.plot(self.dates, self.acc_Zs, label='acc_Z')
		#self.xyz.legend()
		#self.xyz_line = False

		### GRAPHE GxGyGz
		self.GxGyGz=self.fig.add_subplot(231)#, sharex = self.xyz)
		self.GxGyGz.set_title(u'Vitesse angulaire')
		self.GxGyGz.set_xlabel(u'Temps')
		self.GxGyGz.set_ylabel(u'Deg/s')
		self.GxGyGz.plot(self.dates,self.gyro_Xs, label='gyro_X')
		self.GxGyGz.plot(self.dates,self.gyro_Ys, label='gyro_Y')
		self.GxGyGz.plot(self.dates,self.gyro_Zs, label='gyro_Z')
		#self.GxGyGz.set_xticks(self.dates)
		self.GxGyGz.xaxis.set_major_locator(mdates.DayLocator())
		#self.GxGyGz.xaxis.set_minor_locator(mdates.HourLocator())
		self.GxGyGz.xaxis.set_major_formatter(ticker.FormatStrFormatter("%d %b"))
		self.GxGyGz.legend()
		self.GxGyGz_line = False
		#self.fig.autofmt_xdate()
		#plt.xticks(rotation=90)
		logging.debug("GRAPHE GxGyGz ok")

		### GRAPHE INCLINAISON
		self.Inclinaison=self.fig.add_subplot(234, sharex = self.GxGyGz)
		self.Inclinaison.plot(self.dates,self.angle_Ys, label='Inclinaison')
		#self.Inclinaison.legend()
		self.Inclinaison.set_title(u'Inclinaison')
		self.Inclinaison.set_xlabel(u'Temps')
		self.Inclinaison.set_ylabel(u'Deg')
		self.Inclinaison_line = False

		### GRAPHE ROTATION
		self.Rotation=self.fig.add_subplot(235, sharex = self.GxGyGz)
		self.Rotation.plot(self.dates,self.angle_Xs, label='Rotation')
		#self.Rotation.legend()
		self.Rotation.set_title(u'Rotation')
		self.Rotation.set_xlabel(u'Temps')
		self.Rotation.set_ylabel(u'Deg')
		self.Rotation_line = False

		### PHOTO
		self.image_plot = self.fig.add_subplot(232)
		self.image_plot.set_axis_off()
		self.image_plot.set_title(u'Caméra')

		### BOUTONS
		self.fig.canvas.mpl_connect('button_press_event', self.on_click)
		self.bt_lecture = Button(plt.axes([0.65, 0.3, 0.05, 0.03]),'lecture')
		self.bt_lecture.on_clicked(self.on_bt_lecture_click)

		self.bt_lecture10 = Button(plt.axes([0.65, 0.2, 0.05, 0.03]),'lecturex10')
		self.bt_lecture10.on_clicked(self.on_bt_lecture_click10)
		#self.tb_vitesse = TextBox(plt.axes([0.9, 0.8, 0.05, 0.03]),'Vitesse', initial = '1')
		#self.tb_vitesse.on_submit(self.on_tb_vitesse_submit)

		### Détail étape
		axe_etape = self.fig.add_axes([0.65, 0.4, 0.03, 0.03])
		axe_etape.set_axis_off()
		self.etape = plt.text(0,3,u'Etape n° ?')
		self.etape_debut_mvt = plt.text(0,2,u'Début : --')
		self.etape_fin_mvt = plt.text(0,1,u'Fin : --')
		self.etape_acceleration_max = plt.text(0,0,u'Accélération max : --')

		### LEGENDE : FILEUROPE-CMP
		legende = self.fig.add_axes([0.75,0.07,0.2,0.3])
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
		#logging.info("Scan du repertoir images : %s ..."%(rep))
		self.images = {}
		self.images_dates = {}
		if rep:
			for fichier in  os.listdir(rep):
				if os.path.isfile(os.path.join(rep, fichier)):
					try:
						self.images[datetime.datetime.strptime(fichier[3:-4],"%Y-%m-%d %H-%M-%S.%f")]=os.path.join(rep, fichier)
					except:
						pass
			self.images_dates = self.images.keys()
			self.images_dates.sort()
			logging.info("%s images trouvees."%(len(self.images)))
		self.xdate_index = 0

	def show_image(self):
		'''Update the image and the cursors and the etape
		'''
		if len(self.images)>0:
			date = self.images_dates[self.xdate_index]
			image_path = self.images[date]
			#logging.debug("Image %s"%(image_path))
			image_file = cbook.get_sample_data(image_path)
			image = plt.imread(image_file)
			self.image_plot.clear()
			self.image_plot.set_axis_off()
			self.image_plot.imshow(image)
			self.image_plot.set_title(u'Caméra')
			self.image_plot.text(0, 800, "Date : " + self.dates[self.xdate_index].strftime(gyro_ui.format_date))
			if self.GxGyGz_line:
				self.GxGyGz_line.remove()
			self.GxGyGz_line = self.GxGyGz.vlines(date, self.GxGyGz.get_ylim()[0]*0.75, self.GxGyGz.get_ylim()[1]*0.75)
			if self.Inclinaison_line:
				self.Inclinaison_line.remove()
			self.Inclinaison_line = self.Inclinaison.vlines(date, self.Inclinaison.get_ylim()[0]*0.75, self.Inclinaison.get_ylim()[1]*0.75)
			if self.Rotation_line:
				self.Rotation_line.remove()
			self.Rotation_line = self.Rotation.vlines(date, self.Rotation.get_ylim()[0]*0.75, self.Rotation.get_ylim()[1]*0.75)
			etape = self.etapes[self.xdate_index]
			self.etape.set_text(u"Etape n° %s"%etape)
			self.etape_debut_mvt.set_text(u"Début : "+ self.phases[etape]["debut_mvt"].strftime(gyro_ui.format_date))
			self.etape_fin_mvt.set_text(u"Fin : "+ self.phases[etape]["fin_mvt"].strftime(gyro_ui.format_date))
			self.etape_acceleration_max.set_text(u"Accél. max : %s"%self.phases[etape]["acceleration_max"])
			# TODO et plus d'info
			self.fig.canvas.draw()	# C'est ici que c'est long (0.3 s)


	def on_click(self, event):
		'''callback function when click on graphe
		'''
		#logging.debug('button=%d, inaxes = %s, x=%d, y=%d, xdata=%f, ydata=%f' %(event.button, event.inaxes, event.x, event.y, event.xdata, event.ydata))
		if len(self.images)>0:
			if event.inaxes in [self.GxGyGz, self.Inclinaison, self.Rotation] :
				date = mdates.num2date(event.xdata).replace(tzinfo=None)
				#try:
				self.xdate_index = self.images_dates.index(min(self.images_dates, key=lambda d: abs(d-date)))
				logging.debug(self.xdate_index)
				self.show_image()
			#	except:
			#		pass
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
