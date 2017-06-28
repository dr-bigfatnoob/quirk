from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
from collections import OrderedDict
import numpy as np
from utils.lib import O, save_file
from technix.de import DE, Point
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


class StarPoint(O):
  def __init__(self, **params):
    O.__init__(self, **params)

  def __hash__(self):
    return hash(self.id)


class Star(O):
  def __init__(self, model, **settings):
    O.__init__(self)
    self.model = model
    self.settings = default().update(**settings)
    self.de = DE(model, gens=self.settings.k1)

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
    best_size = len(best)
    rest_size = len(rest)
    p_best = best_size / (best_size + rest_size)
    p_rest = rest_size / (best_size + rest_size)
    decisions = []
    best_sols = [self.model.get_solution(sol.decisions) for sol in best]
    rest_sols = [self.model.get_solution(sol.decisions) for sol in rest]
    for d_id, values in self.model.get_decisions().items():
      # Implement Ranks
      best_scores = {v: 0 for v in values}
      for point in best_sols:
        # best_scores[self.model.nodes[point.decisions[d_id]].label] += 1
        best_scores[point[d_id]] += 1
      rest_scores = {v: 0 for v in values}
      for point in rest_sols:
        rest_scores[point[d_id]] += 1
      for key in best_scores.keys():
        l_best = best_scores[key] * p_best / len(best_sols)
        l_rest = rest_scores[key] * p_rest / len(rest_sols)
        sup = 0 if l_best == l_rest == 0 else l_best ** 2 / (l_best + l_rest)
        decisions.append(StarPoint(support=sup,
                                   value=key,
                                   name=d_id))
    decisions.sort(key=lambda x: x.support, reverse=True)
    ranked, aux = [], set()
    for dec in decisions:
      if dec.name not in aux:
        ranked.append(dec)
        aux.add(dec.name)
    assert len(ranked) == len(self.model.get_decisions()), "Mismatch after sorting support"
    return ranked

  def generate(self, presets):
    pop = []
    while len(pop) < self.settings.k2:
      solutions = OrderedDict()
      model = self.model
      if model.decision_map:
        ref = {key: np.random.choice(vals) for key, vals in model.decision_map.items()}
        for key, decision in model.decisions.items():
          if decision.key in presets:
            solutions[key] = decision.options[presets[decision.key]].id
          else:
            solutions[key] = decision.options[ref[decision.key]].id
      else:
        for key, decision in model.decisions.items():
          if key in presets:
            solutions[key] = decision.options[presets[key]].id
          else:
            solutions[key] = np.random.choice(decision.options.values()).id
      pop.append(Point(solutions))
    return pop

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
      population = self.generate(presets)
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


def run(model_name):
  from language.parser import Parser
  mdl = Parser.from_file("models/%s.str" % model_name)
  print("MODEL : %s" % mdl.name)
  star = Star(mdl)
  best, rest = star.sample()
  ranked = star.rank(best, rest)
  print_decisions(ranked, "results/models/%s/top_decisions.md" % mdl.name)
  obj_stats, gens, objective_map = star.prune(ranked)
  star.report(obj_stats, "results/models/%s/star.png" % mdl.name)


if __name__ == "__main__":
  run("ECS")
  run("AOWS")
  run("SAS")



