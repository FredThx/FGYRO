#!/usr/bin/python
# -*- coding: utf-8 -*


from pymongo import MongoClient
import matplotlib.pyplot as plt
import matplotlib.cbook as cbook
import matplotlib.dates as matplotlib_dates
import datetime
from math import atan2, pi
import os
from datetime import datetime
import calendar
from datetime import datetime, timedelta

client = MongoClient('192.168.7.17', 27017)
db = client['fileurope']
gyro = db.gyro




def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)
	
	

dates = []
acc_Xs = []
acc_Ys = []
acc_Zs = []
gyro_Xs = []
gyro_Ys = []
gyro_Zs = []
angle_Xs = []
angle_Ys = []
angle_Zs = []
angle_X = 0
angle_Y = 0
angle_Z = 0

#Lecture des données
for data in gyro.find().sort('date'):
	try:	
		date = utc_to_local(data['date'])
		acc_X = data['acc_X']
		acc_Y = data['acc_Y']
		acc_Z = data['acc_Z']
		gyro_X = data['gyro_X']
		gyro_Y = data['gyro_Y']
		gyro_Z = data['gyro_Z']
		# Calcul angulaire selon accelerometre et pesenteur
		angle_X = atan2(acc_Y,acc_Z) * 180 / pi
		angle_Y = atan2(acc_Z,acc_X) * 180 / pi
		angle_Z = atan2(acc_X,acc_Y) * 180 / pi
		
		# On remplit les tableaux
		dates.append(date)
		acc_Xs.append(acc_X)
		acc_Ys.append(acc_Y)
		acc_Zs.append(acc_Z)
		gyro_Xs.append(gyro_X)
		gyro_Ys.append(gyro_Y)
		gyro_Zs.append(gyro_Z)
		angle_Xs.append(angle_X)
		angle_Ys.append(angle_Y)
		angle_Zs.append(angle_Z)
	except Exception as e:
		print(e)

#Moyenne des vitesses angulaires pour auto-calibration
corr_gyro_Xs = sum(gyro_Xs)/len(gyro_Xs)
corr_gyro_Ys = sum(gyro_Ys)/len(gyro_Ys)
corr_gyro_Zs = sum(gyro_Zs)/len(gyro_Zs)

for i in range(0,len(dates)):
	#Correction des vitesses angulaires
	gyro_Xs[i] -= corr_gyro_Xs
	gyro_Ys[i] -= corr_gyro_Ys
	gyro_Zs[i] -= corr_gyro_Zs
	# "Supression" des mesures d'angle quand il y a une vitesses angulaire
	if i> 0 and (abs(gyro_Xs[i]) > 50 or abs(gyro_Ys[i]) > 50 or abs(gyro_Zs[i]) > 50):
		angle_Xs[i] = angle_Xs[i-1]
		angle_Ys[i] = angle_Ys[i-1]
		angle_Zs[i] = angle_Zs[i-1]
	# Gestion des angles qui passent de pi à -pi
	if abs(angle_Xs[i]-angle_Xs[i-1])>180:
		if angle_Xs[i] < angle_Xs[i-1]:
			angle_Xs[i] += 360
		else:
			angle_Xs[i] -= 360
	if abs(angle_Ys[i]-angle_Ys[i-1])>180:
		if angle_Ys[i] < angle_Ys[i-1]:
			angle_Ys[i] += 360
		else:
			angle_Ys[i] -= 360
	if abs(angle_Zs[i]-angle_Zs[i-1])>180:
		if angle_Zs[i] < angle_Zs[i-1]:
			angle_Zs[i] += 360
		else:
			angle_Zs[i] -= 360

fig = plt.figure()

xyz=fig.add_subplot(221)
#xyz.xlabel('Temps')
#xyz.ylabel('x,y,z')
xyz.plot(dates,acc_Xs, label='acc_X')
xyz.plot(dates,acc_Ys, label='acc_Y')
xyz.plot(dates,acc_Zs, label='acc_Z')
xyz.legend() 
xyz_line = False

GxGyGz=fig.add_subplot(223, sharex = xyz)
#GxGyGz.xlabel('Temps')
#GxGyGz.ylabel('Gx,Gy,Gz')
GxGyGz.plot(dates,gyro_Xs, label='gyro_X')
GxGyGz.plot(dates,gyro_Ys, label='gyro_Y')
GxGyGz.plot(dates,gyro_Zs, label='gyro_Z')
GxGyGz.legend() 
GxGyGz_line = False
	
AxAyAz=fig.add_subplot(224, sharex = xyz)
#AxAyAz.xlabel('Temps')
#AxAyAz.ylabel('Ax,Ay,Az')
AxAyAz.plot(dates,angle_Xs, label='angle_X')
AxAyAz.plot(dates,angle_Ys, label='angle_Y')
AxAyAz.plot(dates,angle_Zs, label='angle_Z')
AxAyAz.legend() 
AxAyAz_line = False


images = {}

def scan_images(rep):
	for fichier in  os.listdir(rep):
		if os.path.isfile(os.path.join(rep, fichier)):
			try:
				images[datetime.strptime(fichier[3:-4],"%Y-%m-%d %H-%M-%S.%f")]=os.path.join(rep, fichier)
			except:
				pass

scan_images('Q:\Frederic\Gyro')

image_file = cbook.get_sample_data(images.values()[0])
image = plt.imread(image_file)
#fig, ax = plt.subplots()
image_plot = fig.add_subplot(222)
image_plot.imshow(image, animated = True)



def find_image(date):
	return images[min(images.keys(), key=lambda d: abs(d-date))]

def onclick(event):
	global xyz_line, AxAyAz_line, GxGyGz_line
	print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %(event.button, event.x, event.y, event.xdata, event.ydata))
	date_photo = matplotlib_dates.num2date(event.xdata).replace(tzinfo=None)
	image_file = cbook.get_sample_data(find_image(date_photo))
	image = plt.imread(image_file)
	image_plot.clear()
	image_plot.imshow(image)
	image_plot.text(0, 0, str(date_photo))
	if xyz_line:
		xyz_line.remove()
	xyz_line = xyz.vlines(event.xdata, xyz.get_ylim()[0]*0.75, xyz.get_ylim()[1]*0.75)
	if AxAyAz_line:
		AxAyAz_line.remove()
	AxAyAz_line = AxAyAz.vlines(event.xdata, AxAyAz.get_ylim()[0]*0.75, AxAyAz.get_ylim()[1]*0.75)
	if GxGyGz_line:
		GxGyGz_line.remove()
	GxGyGz_line = GxGyGz.vlines(event.xdata, GxGyGz.get_ylim()[0]*0.75, GxGyGz.get_ylim()[1]*0.75)
	fig.canvas.draw()
	

cid = fig.canvas.mpl_connect('button_press_event', onclick)

plt.show()
