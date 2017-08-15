from __future__ import print_function, division
import sys
import os

sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

import random
import networkx as nx
from utils.lib import O
from genesis.gen_utils import GraphPoint, Statement, choice


def default():
  """
  Default settings
  :return:
  """
  return O(
    cross_rate=1.0,
    cross_prob=0.4
  )


class Mutator(O):
  def __init__(self, model, **settings):
    self.model = model
    self.settings = default().update(**settings)
    O.__init__(self)

  def mutate_random(self, point, population):
    """
    Just another random point
    :param point:
    :param population:
    :return:
    """
    other = GraphPoint(self.model.generate())
    other.evaluate(self.model)
    while other in population or other == point:
      other = GraphPoint(self.model.generate())
      other.evaluate(self.model)
    return other

  def cross_over(self, point_a, point_b):
    """
    Cris-Cross Crossover
    :param point_a:
    :param point_b:
    :return: new instance of GraphPoint
    """
    if random.random() > self.settings.cross_rate:
      return point_a
    graph = nx.DiGraph()
    model = self.model
    graph.add_nodes_from(model.vocabulary.nodes)
    for stmt in model.positives:
      graph.add_edge(stmt.source, stmt.target, relation=stmt.relation)
    existing = set(list(model.positives) + list(model.negatives))
    while not nx.is_weakly_connected(graph):
      stmt = None
      while stmt is None or stmt in existing:
        cross_prob = random.random()
        if cross_prob < self.settings.cross_prob:
          edge = choice(point_a.decisions.edges(data=True))
          stmt = Statement(edge[0], edge[2]['relation'], edge[1])
        elif self.settings.cross_prob <= cross_prob < 2 * self.settings.cross_prob:
          edge = choice(point_b.decisions.edges(data=True))
          stmt = Statement(edge[0], edge[2]['relation'], edge[1])
        else:
          target = choice(model.vocabulary.nodes)
          in_edges = graph.in_edges([target], data=True)
          if in_edges:
            relations = set([edge[2]['relation'] for edge in in_edges])
            assert len(relations) == 1, "Multiple incoming relations to node %s" % target
            relation = choice(relations)
          else:
            relation = choice(model.vocabulary.edges)
          source = target
          while source == target:
            source = choice(model.vocabulary.nodes)
          # Checking if edge or its reverse does not exist in graph
          if graph.has_edge(source, target) or graph.has_edge(target, source):
            stmt = None
          else:
            stmt = Statement(source, relation, target)
      graph.add_edge(stmt.source, stmt.target, relation=stmt.relation)
      if not model.cycle_exists(graph):
        existing.add(stmt)
      else:
        graph.remove_edge(stmt.source, stmt.target)
    return GraphPoint(graph)

  @staticmethod
  def mutate_do_nothing(point, population):
    return point.clone()
