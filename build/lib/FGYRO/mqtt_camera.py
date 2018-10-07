#!/usr/bin/python
# -*- coding: utf-8 -*

import picamera
import datetime
import time
import paho.mqtt.client as paho
import socket

#Pour travailler sur les sources
import sys
sys.path.insert(0,'../FUTIL')
from FUTIL.my_logging import *

#TODO : reconnection mqtt

class mqtt_camera(object):
	''' Une camera raspberry pi pilotée par messages mqtt
	'''
	CAPTURE_IMAGE = "image"
	CAPTURE_VIDEO = "video"
	
	def __init__(self, mqtt_host='127.0.0.1', mqtt_port=1883, mqtt_base_topic = 'CAM', image_folder = '', video_folder = None, video_duration = 5, leds = None):
		'''Initialisation
			mqtt_host			:	mqtt host. default = localhost
			mqtt_port			:	default = 1883
			mqtt_base_topic		:	mqtt topic listened
			image_folder
			video_forder
			video_duration		:	duration of recording video en seconds (default : 5s)
			leds				: 	FGPIO.led_io 
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
		self.init_camera()
		self.leds = leds
		self.mqtt_connect()
	
	def init_camera(self)
		'''Try to start the camera
		'''
		if not self.camera:
			try:
				self.camera = picamera.PiCamera()
				self.camera.led = False
			except:
				pass
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
		if self.leds:
			self.leds.on()
			time.sleep(0.05)
		file = self.image_folder + 'img' + str(datetime.datetime.now()).replace(':','-') + '.png'
		logging.debug("Image %s capturée"%file)
		self.init_camera()
		if self.camera:
			self.camera.capture(file, format = 'png')
		if self.leds:
			self.leds.off()
	
	def captureVideo(self, duration = None):
		'''Capture a short Video 
			- duration		: duration of recording video en seconds (default : mqtt_camera duration)
		'''
		if self.leds:
			self.leds.on()
		if not duration:
			duration = self.video_duration
		file = self.video_folder + 'vid' + str(datetime.datetime.now()).replace(':','-') + '.h264'
		logging.debug("Video start...")
		self.init_camera()
		if self.camera:
			self.camera.start_recording(file, format = 'h264')
			time.sleep(duration)
			self.camera.stop_recording()
		logging.debug("Video %s capturée"%file)
		if self.leds:
			self.leds.off()
	
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
			except:
				time.sleep(5)
				
	
if __name__ == '__main__':
	my_logging(console_level = DEBUG, logfile_level = DEBUG, details = False)	
	cam = mqtt_camera(image_folder = './capture/', mqtt_base_topic = 'FILEUROPE/CAM')
	cam.loop_forever()

		