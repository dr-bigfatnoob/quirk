from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from utils.lib import mkdir


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
  directory = fig_name.rsplit("/", 1)[0]
  mkdir(directory)
  plt.savefig(fig_name, bbox_inches='tight')


def med_spread_plot(data, obj_names, fig_name="temp.png"):
  fig = plt.figure(1)
  fig.subplots_adjust(hspace=0.5)
  directory = fig_name.rsplit("/", 1)[0]
  mkdir(directory)
  for i, (key, data_map) in enumerate(data.items()):
    meds = data_map["meds"]
    iqrs = data_map.get("iqrs", None)
    if iqrs:
      x = range(len(meds))
      index = int(str(len(data)) + "1" + str(i + 1))
      plt.subplot(index)
      plt.title(obj_names[key])
      plt.plot(x, meds, 'b-', x, iqrs, 'r-')
      # plt.ylim((min(iqrs) - 1, max(meds) + 1))
    else:
      x = range(len(meds))
      index = int(str(len(data)) + "1" + str(i + 1))
      plt.subplot(index)
      plt.title(obj_names[key])
      plt.plot(x, meds, 'b-')
      # plt.ylim((min(meds) - 1, max(meds) + 1))
  blue_line = mlines.Line2D([], [], color='blue', label='Median')
  red_line = mlines.Line2D([], [], color='red', label='IQR')
  plt.figlegend((blue_line, red_line), ('Median', 'IQR'), loc=9, bbox_to_anchor=(0.5, 0.075), ncol=2)
  plt.savefig(fig_name, bbox_inches='tight')
  plt.clf()
