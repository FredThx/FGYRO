#!/usr/bin/python
# -*- coding: utf-8 -*

"""
============
3D animation
============

A simple example of an animated plot... In 3D!
"""
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.axes3d as p3
import matplotlib.animation as animation


# Attaching 3D axis to the figure
fig = plt.figure()
ax = p3.Axes3D(fig)

lignes = []
#Fond fil
for i in range(0,11):
	lignes.append([[0.1*i,0,0],[0.1*i,0,1],'blue'])
lignes.append([[0,0,1],[0,1,1],'red'])
lignes.append([[0,1,1],[0,1,0],'red'])
lignes.append([[0,1,0],[1,1,0],'red'])
lignes.append([[1,1,0],[1,0,0],'red'])
lignes.append([[1,0,1],[1,1,1],'red'])
lignes.append([[1,1,1],[1,1,0],'red'])

# Creating fifty line objects.
# NOTE: Can't pass empty arrays into 3d version of plot()
lines = [ax.plot([ligne[0][0],ligne[1][0]],[ligne[0][1],ligne[1][1]],[ligne[0][2],ligne[1][2]],color=ligne[2])[0] for ligne in lignes]

# Setting the axes properties
ax.set_xlim3d([-0.1, 1.1])
ax.set_xlabel('X')

ax.set_ylim3d([-0.1, 1.1])
ax.set_ylabel('Y')

ax.set_zlim3d([-0.1, 1.1])
ax.set_zlabel('Z')

ax.set_title('3D Test')

while True:
	for angle in range(0, 360):
		ax.view_init((angle%60)*6, angle)
		plt.draw()
		plt.pause(.001)