from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
import random
from utils.lib import say

__author__ = "bigfatnoob"


def loo(points):
  for i in range(len(points)):
    one = points[i]
    rest = points[:i] + points[i+1:]
    yield one, rest


def nsga2(model, mutator, population, tournament_size=4, iterations=100):
  k = len(population)
  [one.evaluate(model) for one in population]
  for _ in range(iterations):
    say(".")
    population = evolve(model, mutator, population, tournament_size)
    population = select(model, population, k)
  return population


def select(model, population, k):
  """
  Select top k points from population.
  :param model: Instance of model
  :param population: List of points
  :param k: Number of points to select
  :return: Top k points
  """
  if len(population) < k:
    return population
  [point.evaluate(model) for point in population]
  fronts = sort_non_dominated(model, population)
  pop_next = []
  for i, front in enumerate(fronts):
    if len(pop_next) + len(fronts[i]) >= k:
      fronts[i] = assign_crowd_dist(model, front)
      pop_next += sorted(fronts[i], key=lambda x: x.crowd_dist, reverse=True)[:(k - len(pop_next))]
      break
    else:
      pop_next += fronts[i]
  return pop_next


def evolve(model, mutator, population, tournament_size=4):
  """
  Performs crossover and mutation and doubles population size
  :param model: Instance of Model
  :param mutator: Instance of Mutator
  :param population: List of points
  :param tournament_size: Size of tournament
  :return: List of population + List of mutants
  """
  kids = []
  clones = [one.clone() for one in population]
  for _ in xrange(len(clones)):
    mom = binary_tournament_selection(model, population, tournament_size)
    while True:
      dad = binary_tournament_selection(model, population, tournament_size)
      if not mom == dad: break
    kid = mutator.cross_over(mom, dad)
    kid = mutator.mutate(kid, population)
    kids.append(kid)
  return clones + kids


def binary_tournament_selection(model, population, size):
  """
  Select individual from the population of size
  tourn_size based on tournament evaluation
  :param model: Model used for evaluation
  :param population: Population to sample from
  :param size: Size of tournament
  :return: Most dominant individual from the tournament
  """
  tournament = random.sample(population, size)
  best = tournament[0]
  for i in range(1, len(tournament)):
    if model.better(tournament[i], best) == 1:
      best = tournament[i]
  return best


def sort_non_dominated(model, population):
  frontiers = []
  front1 = []
  i = 1
  for one, rest in loo(population):
    i += 1
    for two in rest:
      domination_status = domination(model, one, two)
      if domination_status == 1:
        one.dominated.append(two)
      elif domination_status == 2:
        one.dominating += 1
    if one.dominating == 0:
      one.rank = 1
      front1.append(one)
  current_rank = 1
  frontiers.append(front1)
  while True:
    front2 = []
    for one in front1:
      for two in one.dominated:
        two.dominating -= 1
        if two.dominating == 0:
          two.rank = current_rank + 1
          front2.append(two)
    current_rank += 1
    if len(front2) == 0:
      break
    else:
      frontiers.append(front2)
      front1 = front2
  return frontiers


def domination(model, one, two):
  """
  Domination is defined as follows:
  for all objectives a in "one" and
  all objectives b in "two"
  every a <= b
  for all objectives a in "one" and
  all objectives b in "two"
  at least one a < b
  Check if one set of decisions ("one")
  dominates other set of decisions ("two")
  Returns:
    0 - one and two are not better each other
    1 - one better than two
    2 - two better than one
  """
  one_status, one_offset = model.evaluate_constraints(one.decisions)
  two_status, two_offset = model.evaluate_constraints(two.decisions)
  if one_status and two_status:
    # Return the better solution if both solutions satisfy the constraints
    return model.better(one.objectives, two.objectives)
  elif one_status:
    # Return 1, if 1 satisfies the constraints
    return 1
  elif two_status:
    # Return 2, if 2 satisfies the constraints
    return 2
  # both fail the constraints
  elif one_offset < two_offset:
    # one has a lesser offset deviation
    return 1
  elif one_offset > two_offset:
    # two has a lesser offset deviation
    return 2
  else:
    return random.choice([1, 2])


def assign_crowd_dist(model, frontier):
  """
  Crowding distance between each point in
  a frontier.
  """
  l = len(frontier)
  for m in model.objectives.keys():
    frontier = sorted(frontier, key=lambda x: x.objectives[m])
    vals = [pt.objectives[m] for pt in frontier]
    up = max(vals)
    down = min(vals)
    frontier[0].crowd_dist = float("inf")
    frontier[-1].crowd_dist = float("inf")
    for i in range(1, l - 1):
      frontier[i].crowd_dist += (normalize(frontier[i + 1].objectives[m], up, down) -
                                 normalize(frontier[i - 1].objectives[m], up, down))
  return frontier


def normalize(val, up, down):
  if up == down:
    return 0
  return (val - down) / (up - down)


def _main(model_name):
  from language.parser import Parser
  from language.mutator import Mutator
  from technix.de import DE
  mdl = Parser.from_file("models/%s.str" % model_name)
  mdl.initialize()
  de = DE(mdl, Mutator)
  pop = de.populate(10)
  [point.evaluate(mdl) for point in pop]
  pop_sorted = select(mdl, pop, len(pop))
  assert mdl.bdom(pop_sorted[0].objectives, pop_sorted[-1].objectives) in [0, 1]


if __name__ == "__main__":
  _main("ECS")
