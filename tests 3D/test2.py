from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
from itertools import product, combinations
from math import sin
from math import cos

fig = plt.figure()
ax = fig.gca(projection='3d')
ax.set_aspect("equal")

# draw cube
r = [-1, 1]
for s, e in combinations(np.array(list(product(r, r, r))), 2):
	if np.sum(np.abs(s-e)) == r[1]-r[0]:
		ax.plot3D(*zip(s, e), color="b")

# draw sphere
#u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
#x = np.cos(u)*np.sin(v)
#y = np.sin(u)*np.sin(v)
#z = np.cos(v)
#ax.plot_wireframe(x, y, z, color="r")

# draw a point
ax.scatter([0], [0], [0], color="g", s=100)

# draw a vector
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d
from matplotlib.widgets import Button


class Arrow3D(FancyArrowPatch):

	def __init__(self, angleX, angleY, angleZ, *args, **kwargs):
		FancyArrowPatch.__init__(self, (0, 0), (0, 0), *args, **kwargs)
		self.set_verts3d(angleX, angleY, angleZ)

	def set_verts3d(self, angleX, angleY, angleZ):
		self.angleX = angleX
		self.angleY = angleY
		self.angleZ = angleZ
		self._verts3d = [0,cos(angleZ)], [0, sin(angleZ)], [0,cos(angleY)]
	
	def draw(self, renderer):
		xs3d, ys3d, zs3d = self._verts3d
		xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, renderer.M)
		self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
		FancyArrowPatch.draw(self, renderer)
	def rotateZ(self,vz=0.1):
		self.set_verts3d(self.angleX, self.angleY, self.angleZ + vz)
		print(self.angleX , self.angleY, self.angleZ,self._verts3d)

a = Arrow3D(0,0,0, mutation_scale=20,
			lw=1, arrowstyle="-|>", color="k")
ax.add_artist(a)


def on_Bt_Xplus_click(event):
	a.rotateZ()
	plt.draw()

Bt_Xplus = Button(plt.axes([0.9, 0.3, 0.08, 0.05]),'X+')
Bt_Xplus.on_clicked(on_Bt_Xplus_click)

if __name__ == "__main__":
	plt.show()