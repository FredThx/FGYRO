#!/usr/bin/python
# -*- coding: utf-8 -*

import picamera
import datetime
import time
import paho.mqtt.client as paho
import socket
from FGPIO.f_thread import *

#Pour travailler sur les sources
import sys
sys.path.insert(0,'../FUTIL')
from FUTIL.my_logging import *

#TODO : reconnection mqtt

# Pour améliorer la qualité de la photo et maintenir un niveau de batterie ok
# - Eteindre la camera qu'après un timeout
#		On peut mettre ça dans le loop_forever	(voir http://www.steves-internet-guide.com/loop-python-mqtt-client/)
# - Si la caméra a été eteinte : augmenter pause pour mise au point (ou trouver algo du type camera.mise_au_point())
# - Si la camera n'a pas été éteinte : plus petite pause
# Peut-on empecher le mode auto de la camera (et ne l'utiliser que lors de la sortie de veille)
# => on gagne le temps de passage du noir à la lumière
# mode radar auto : une photo avec leds au mini et une photo avec led au maxi + reconstitution d'une image améliorée.



class mqtt_camera(object):
	''' Une camera raspberry pi pilotée par messages mqtt
	'''
	CAPTURE_IMAGE = "image"
	CAPTURE_VIDEO = "video"

	def __init__(self, mqtt_host='127.0.0.1', mqtt_port=1883, mqtt_base_topic = 'CAM', image_folder = '', video_folder = None, video_duration = 5, leds = None, tempo = 2.5, camera_timeout = 5):
		'''Initialisation
			mqtt_host			:	mqtt host. default = localhost
			mqtt_port			:	default = 1883
			mqtt_base_topic		:	mqtt topic listened
			image_folder
			video_forder
			video_duration		:	duration of recording video en seconds (default : 5s)
			leds			: 	FGPIO.led_io
			tempo			:	temporisation (secondes) entre leds on et capture photo
		'''
		self.mqtt_host = mqtt_host
		self.mqtt_port = mqtt_port
		self.mqtt_base_topic = mqtt_base_topic
		if self.mqtt_base_topic:
			if self.mqtt_base_topic != '' and self.mqtt_base_topic[-1]!='/':
				self.mqtt_base_topic = self.mqtt_base_topic + '/'
		self.mqtt_client = paho.Client()
		self.mqtt_client.on_connect = self.on_mqtt_connect
		self.mqtt_client.on_message = self.on_mqtt_message
		self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
		#todo : faire getter/setter
		self.image_folder = image_folder
		if self.image_folder != '' and self.image_folder[-1]!= '/':
			self.image_folder += '/'
		if video_folder:
			self.video_folder = video_folder
			if self.video_forder != '' and self.image_folder[-1]!= '/':
				self.video_folder += '/'
		else:
			self.video_folder = self.image_folder
		self.video_duration = video_duration
		self.camera = None
		self.thread = None
		self.status = "stop"
		self.starting_time = 0
		self.leds = leds
		self.init_time_camera = tempo
		self.camera_timeout = camera_timeout
		self.init_camera()
		self.mqtt_connect()

	def init_camera(self):
		'''Start the camera and the leds
		if the camera is not started,
			start it
			switch on the leds
			wait for self.init_time_camera
		execute un thread qui va éteindre la camera et les leds
		'''
		logging.debug('Camera status : %s.'%self.status)
		if self.status == 'stop' or not self.camera or self.camera.closed:
			self.status = 'starting'
			logging.debug('Camera status : %s.'%self.status)
			if self.leds:
				self.leds.on()
			try:
				self.camera = picamera.PiCamera() # TODO : pour affiner resolution, ...
				self.camera.led = False
			except:
				pass
			self.starting_time = time.time()
			time.sleep(self.init_time_camera)
			self.thread_end_time = time.time() + self.camera_timeout
			self.status = 'start'
			logging.debug('Camera status : %s.'%self.status)
			self.thread = f_thread(self._stop_camera)
			self.thread.start()
			return True
		elif self.status == 'starting':
			logging.debug('Camera status : %s.'%self.status)
			return False
		else:
			logging.debug('Camera status : %s.'%self.status)
			self.thread_end_time = time.time() + self.camera_timeout
			return True


	def _stop_camera(self):
		'''for threading
		'''
		if time.time() > self.thread_end_time:
			self.stop_camera()
			self.thread.stop()
			self.thread = None
		else:
			time.sleep(0.05)

	def stop_camera(self):
		'''Stop the camera and the leds
		'''
		if self.leds:
			self.leds.off()
		if self.camera:
			self.camera.close()
		self.status = 'stop'
		logging.debug('Camera status : %s.'%self.status)

	def mqtt_connect(self):
		'''Connect to the MQTT broker
		'''
		is_connected = False
		while is_connected == False:
			try:
				self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 30)
				is_connected = True
			except socket.error:
				logging.error("Mqtt server : Connection refused")
				time.sleep(30)
				logging.error("Mqtt server : re-connection...")

	def captureImage(self):
		'''Capture image
		'''
		#TODO : peut etre format de date en UTC (pour éviter pbs de changement heure)
		logging.debug("captureImage start...")
		if self.init_camera():
			file = self.image_folder + 'img' + str(datetime.datetime.now()).replace(':','-') + '.png'
			if self.camera:
				self.camera.capture(file, format = 'png')
				logging.debug("Image %s captured"%file)
				self.mqtt_send(self.mqtt_base_topic+'png_stored',file)
			else:
				logging.debug("Camera Error. Image not captured")
		else:
			logging.debug("Camera buzy. Image not captured")

	def captureVideo(self, duration = None):
		'''Capture a short Video
			- duration		: duration of recording video en seconds (default : mqtt_camera duration)
		'''
		self.init_camera()
		if not duration:
			duration = self.video_duration
		file = self.video_folder + 'vid' + str(datetime.datetime.now()).replace(':','-') + '.h264'
		logging.debug("Video start...")
		if self.camera:
			self.camera.start_recording(file, format = 'h264')
			time.sleep(duration)
			self.camera.stop_recording()
		logging.debug("Video %s capturée"%file)

	def mqtt_send(self, topic, payload):
		'''Send a mqtt message
		'''
		logging.debug("MQTT SEND topic : %s , payload : %s"%(topic, payload))
		try:
			self.mqtt_client.reconnect()
			self.mqtt_client.publish(topic, payload)
		except socket.error:
			logging.error("Mqtt server : Connection refused")

	def on_mqtt_connect(self, client, userdata, flags, rc):
		'''Callback function on_connect
		'''
		logging.info("MQTT connected")
		self.mqtt_client.subscribe(self.mqtt_base_topic+"#")
		logging.debug("MQTT subscribe : %s"%self.mqtt_base_topic+"#")


	def on_mqtt_message(self, client, userdata, msg):
		'''Callback function on_message
		'''
		logging.debug('MQTT message received : %s => %s'%(msg.topic, msg.payload))
		if msg.payload.upper() == self.CAPTURE_IMAGE.upper():
			self.captureImage()
		elif msg.payload.upper() == self.CAPTURE_VIDEO.upper():
			self.captureVideo()

	def on_mqtt_disconnect(self, client, userdata, rc):
		'''Callback function on_disconnect
		'''
		logging.error("MQTT disconnected. Error code : %s."%(rc))
		time.sleep(30)
		logging.error("MQTT : trying reconnect")
		self.mqtt_client.reconnect()

	def loop_forever(self):
		'''loop forever and wait mqtt messages
		'''
		while True:
			try:
				self.mqtt_client.loop_forever()
			except Exception as e:
				logging.debug("Error on mqtt_client.loop_forever() : %s"%e)
				time.sleep(2)


if __name__ == '__main__':
	my_logging(console_level = DEBUG, logfile_level = DEBUG, details = False)
	cam = mqtt_camera(image_folder = './capture/', mqtt_base_topic = 'FILEUROPE/CAM')
	cam.loop_forever()
