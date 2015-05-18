from __future__ import division
from pySDC.Hooks import hooks
from pySDC.Stats import stats

import matplotlib.pyplot as plt
import numpy as np

from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter

class plot_solution(hooks):

    def __init__(self):
        """
        Initialization of output
        """
        super(plot_solution,self).__init__()

        # add figure object for further use
        #        self.fig = plt.figure(figsize=(18,6))
        self.fig = plt.figure(figsize=(9,9))


    def dump_step(self,status):
        """
        Overwrite standard dump per step

        Args:
            status: status object per step
        """
        super(plot_solution,self).dump_step(status)

        yplot = self.level.uend.values
        xx    = self.level.prob.xx
        zz    = self.level.prob.zz
        self.fig.clear()
        CS = plt.contourf(xx, zz, yplot[2,:,:], rstride=1, cstride=1, cmap=cm.coolwarm, linewidth=0, antialiased=False)
        cbar = plt.colorbar(CS)
        plt.axes().set_xlim(xmin = self.level.prob.x_b[0], xmax = self.level.prob.x_b[1])
        plt.axes().set_ylim(ymin = self.level.prob.z_b[0], ymax = self.level.prob.z_b[1])
        plt.axes().set_aspect('equal')
        plt.xlabel('x')
        plt.ylabel('z')
        #plt.tight_layout()
        plt.show(block=False)
        plt.pause(0.00001)

        return None
