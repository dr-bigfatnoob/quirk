from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
import numpy as np
from utils.lib import O, save_file
from technix.de import DE
from technix import nsga
from utils import plotter
from prettytable import PrettyTable

__author__ = "bigfatnoob"


def default():
  return O(
      k1=20,
      k2=100,
      best_percent=25,
      gen_step=2
  )


def med_iqr(lst):
  return np.median(lst), np.percentile(lst, 75) - np.percentile(lst, 25)

class Star(O):
  def __init__(self, model, mutator, **settings):
    O.__init__(self)
    self.model = model
    self.settings = default().update(**settings)
    self.de = DE(model, mutator, gens=self.settings.k1)

  def plot_pareto(self, stat):
    obj_ids = self.model.objectives.keys()
    gens_obj_start = stat.get_objectives(0, obj_ids)
    gens_obj_end = stat.get_objectives(-1, obj_ids)
    plotter.plot_pareto([gens_obj_start, gens_obj_end], ['red', 'green'], ['x', 'o'],
                        ['first', 'last'], obj_ids[0], obj_ids[1], 'Pareto Front',
                        'results/models/%s/pareto.png' % self.model.name)

  def sample(self):
    print("Sampling ... ")
    stat = self.de.run()
    self.plot_pareto(stat)
    population = set()
    for point in stat.generations[0] + stat.generations[1] + stat.generations[-1]:
      population.add(point)
    best = set(nsga.select(self.model, list(population), int(len(population) * self.settings.best_percent / 100)))
    rest = population - best
    return best, rest

  def rank(self, best, rest):
    print("Ranking ... ")
    return self.de.mutator.decision_ranker(best, rest)

  def objective_stats(self, generations):
    stats = {}
    objective_map = {}
    for key in self.model.objectives.keys():
      objectives = []
      data_map = {}
      meds = []
      iqrs = []
      for gen, pop in enumerate(generations):
        objs = [pt.objectives[key] for pt in pop]
        objectives.append(objs)
        med, iqr = med_iqr(objs)
        meds.append(med)
        iqrs.append(iqr)
      objective_map[key] = objectives
      data_map["meds"] = meds
      data_map["iqrs"] = iqrs
      stats[key] = data_map
    return stats, objective_map

  def prune(self, supports):
    print("Pruning ... ")
    gens = []
    for i in xrange(len(supports) + 1):
      presets = {sup.name: sup.value for sup in supports[:i]}
      population = self.de.mutator.generate(presets, self.settings.k2)
      [point.evaluate(self.model) for point in population]
      gens.append(population)
    obj_stats, objective_map = self.objective_stats(gens)
    return obj_stats, gens, objective_map

  def report(self, stats, fig_name):
    print("Reporting ... ")
    headers = {key: self.model.objectives[key].name for key in stats.keys()}
    plotter.med_spread_plot(stats, headers, fig_name)


def print_decisions(decisions, file_name=None):
  columns = ["rank", "name", "value", "support"]
  table = PrettyTable(columns)
  for i, decision in enumerate(decisions):
    row = [i + 1, decision.name, decision.value, round(decision.support, 5)]
    table.add_row(row)
  if file_name:
    text = "\n### Decisions Ranked"
    text += "\n```\n"
    text += str(table)
    text += "\n```\n"
    save_file(text, file_name)
  else:
    print("\n### Decisions Ranked")
    print("```")
    print(table)
    print("```")


def run_quirk(model_name):
  from language.parser import Parser
  from language.mutator import Mutator
  mdl = Parser.from_file("models/quirk/%s.str" % model_name)
  print("MODEL : %s" % mdl.name)
  star = Star(mdl, Mutator)
  best, rest = star.sample()
  ranked = star.rank(best, rest)
  print_decisions(ranked, "results/models/%s/top_decisions.md" % mdl.name)
  obj_stats, gens, objective_map = star.prune(ranked)
  star.report(obj_stats, "results/models/%s/star.png" % mdl.name)


def run_xomo():
  from models.xomo.xomo import Model
  from models.xomo.mutator import Mutator
  mdl = Model()
  star = Star(mdl, Mutator)
  best, rest = star.sample()
  ranked = star.rank(best, rest)
  print_decisions(ranked, "results/models/%s/top_decisions.md" % mdl.name)
  obj_stats, gens, objective_map = star.prune(ranked)
  star.report(obj_stats, "results/models/%s/star.png" % mdl.name)

if __name__ == "__main__":
  run_xomo()
  exit()
  run_quirk("ECS")
  run_quirk("AOWS")
  run_quirk("SAS")
