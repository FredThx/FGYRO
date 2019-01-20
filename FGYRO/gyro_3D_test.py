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
	def __init__(self, *args, **kwargs):
		Figure.__init__(self, *args, **kwargs)
		self.ax = self.gca(projection='3d')
		self.ax.set_aspect("equal")
		self.ax.set_xlim(-1,1)
		self.ax.set_ylim(-1,1)
		self.ax.set_zlim(-1,1)
		self.ax.scatter([0], [0], [0], color="g", s=100)
		self.object = Arrow3D(0,0,0, mutation_scale=20,
			lw=1, arrowstyle="-|>", color="k")
		self.ax.add_artist(self.object)
		
	def set_angles(self, *args, **kwargs):
		self.object(set_verts3d(*args, **kwargs))


class Arrow3D(FancyArrowPatch):

	def __init__(self, angleX, angleY, angleZ, *args, **kwargs):
		FancyArrowPatch.__init__(self, (0, 0), (0, 0), *args, **kwargs)
		self.set_verts3d(angleX, angleY, angleZ)

	def set_verts3d(self, angleX, angleY, angleZ):
		self.angleX = angleX
		self.angleY = angleY
		self.angleZ = angleZ
		self._verts3d = [0,0.5*cos(angleZ)], [0, 0.5*sin(angleZ)], [0,0.5*cos(angleY)]
	
	def draw(self, renderer):
		xs3d, ys3d, zs3d = self._verts3d
		xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, renderer.M)
		self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
		FancyArrowPatch.draw(self, renderer)
	def rotateZ(self,vz=0.1):
		self.set_verts3d(self.angleX, self.angleY, self.angleZ + vz)
		print(int((self.angleX*180.0/pi)%360) , int((self.angleY*180.0/pi)%360), int((self.angleZ*180.0/pi)%360),self._verts3d)
	def rotateY(self,vy=0.1):
		self.set_verts3d(self.angleX, self.angleY+vy, self.angleZ)
		print(int((self.angleX*180.0/pi)%360) , int((self.angleY*180.0/pi)%360), int((self.angleZ*180.0/pi)%360),self._verts3d)



def on_Bt_Zplus_click(event):
	o.object.rotateZ()
	plt.draw()
def on_Bt_Yplus_click(event):
	o.object.rotateY()
	plt.draw()

if __name__ == "__main__":
	o = plt.figure(FigureClass = figure3D)
	Bt_Zplus = Button(plt.axes([0.9, 0.3, 0.08, 0.05]),'Z+')
	Bt_Zplus.on_clicked(on_Bt_Zplus_click)
	Bt_Yplus = Button(plt.axes([0.9, 0.5, 0.08, 0.05]),'Y+')
	Bt_Yplus.on_clicked(on_Bt_Yplus_click)
	plt.show()