from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
from itertools import product, combinations
from math import sin, cos, pi
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d
from matplotlib.widgets import Button

class figure3D(Figure):
	'''Une figure matplotlib qui contient un object montrant la position dans l'espace
	'''
	def __init__(self, Acc_X = 0, Acc_Y = 1, Acc_Z = 0,*args, **kwargs):
		Figure.__init__(self, *args, **kwargs)
		self.ax = self.gca(projection='3d')
		self.ax.set_aspect("equal")
		self.ax.set_xlim(-1,1)
		self.ax.set_ylim(-1,1)
		self.ax.set_zlim(-1,1)
		self.ax.scatter([0], [0], [0], color="g", s=100)
		self.object = object3D(Acc_X,Acc_Y,Acc_Y)
		self.ax.add_artist(self.object)
		
	def set_accelation(self, Acc_X, Acc_Y, Acc_Z):
		self.object.set_accelation(Acc_X, Acc_Y, Acc_Z)


class object3D(FancyArrowPatch):

	def __init__(self, Acc_X, Acc_Y, Acc_Z, *args, **kwargs):
		FancyArrowPatch.__init__(self, (0, 0), (0, 0), *args, **kwargs)
		self.set_position(Acc_X, Acc_Y, Acc_Z)

	def set_accelation(self, Acc_X, Acc_Y, Acc_Z):
		'''Defini la position dans l'espace à partir des composantes de la gravité selon x,y,z
		'''
		#TODO
		pass
	
	def draw(self, renderer):
		xs3d, ys3d, zs3d = self._verts3d
		xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, renderer.M)
		self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
		FancyArrowPatch.draw(self, renderer)
