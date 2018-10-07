FGYRO Lib  Fred GYRO lib
========================================================================

	Pour Simulation GYRO

	Hardware :
		- Raspberry Pi 
		- camera pi
		- leds
	
	Software :
		- lib FUTIL
		- python
		- mqtt server (like mosquitto)
		- optional node-RED
		

Installation :
     pip install FGYRO
	 (create a /opt/FGYRO directory for main program)
	 
Configuration :
	change main.py

 automatisation (jessie) :
	sudo systemctl enable fgyro.service
