from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
from utils.lib import O
from utils.sk import rdivDemo
from prettytable import PrettyTable

__author__ = "bigfatnoob"


def median_iqr(lst, ordered=False):
  if not ordered:
    lst = sorted(lst)
  n = len(lst)
  q = n // 4
  iqr = lst[q * 3] - lst[q]
  if n % 2:
    return lst[q * 2], iqr
  else:
    p = max(0, q - 1)
    return (lst[p] + lst[q]) * 0.5, iqr


class Statistics(O):
  @staticmethod
  def default_settings():
    return O(
        gen_step=20
    )

  def __init__(self, settings=None):
    O.__init__(self)
    self.generations = []
    self.runtime = 0
    if not settings:
      settings = Statistics.default_settings()
    self.settings = settings

  def insert(self, pop):
    self.generations.append(pop)
    return self

  def tiles(self):
    num_obs = len(self.generations[0][0].objectives)
    for i in range(num_obs):
      obj_gens = []
      for gen, pop in enumerate(self.generations):
        if gen % self.settings.gen_step != 0:
          continue
        objs = ["gen%d_f%d" % (gen, i + 1)]
        for point in pop:
          objs.append(point.objectives[i])
        obj_gens.append(objs)
      rdivDemo(obj_gens)

  def median_spread(self):
    num_obs = len(self.generations[0][0].objectives)
    data = []
    for i in range(num_obs):
      data_map = {}
      meds = []
      iqrs = []
      for gen, pop in enumerate(self.generations):
        objs = [pt.objectives[i] for pt in pop]
        med, iqr = median_iqr(objs)
        meds.append(med)
        iqrs.append(iqr)
      data_map["meds"] = meds
      data_map["iqrs"] = iqrs
      data.append(data_map)
    return data

  def spit_objectives(self):
    objectives = []
    for point in self.generations[-1]:
      objectives.append(point.objectives)
    return objectives

  @staticmethod
  def tabulate(columns, pt):
    tab = PrettyTable(columns)
    tab.align["name"] = "l"
    nodes = pt.get_nodes()
    for node in nodes:
      row = []
      for key in columns:
        row.append(node.has()[key])
      tab.add_row(row)
    print(tab)

  def get_objectives(self, index, obj_ids):
    return [[point.objectives[obj_id] for obj_id in obj_ids] for point in self.generations[index]]
