from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

import matplotlib.pyplot as plt


def plot_pareto(generations, colors, markers, labels, x_label, y_label, title, fig_name):
  assert len(generations) == len(colors) == len(markers) == len(labels)
  for i in xrange(len(generations)):
    gen = generations[i]
    x_axis, y_axis = [], []
    for j in xrange(len(gen)):
       x_axis.append(gen[j][0])
       y_axis.append(gen[j][1])
    plt.plot(x_axis, y_axis, color=colors[i], marker=markers[i], label=labels[i], linestyle='')
  plt.xlabel(x_label)
  plt.ylabel(y_label)
  plt.title(title)
  plt.savefig(fig_name, bbox_inches='tight')
