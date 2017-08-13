from __future__ import print_function, division
import sys
import os

sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

import networkx as nx
from utils.lib import O

__author__ = "bigfatnoob"


class Objective(O):
  """
  Objective for a model
  """
  def __init__(self, name, direction, evaluation):
    O.__init__(self)
    self.name = name
    self.direction = direction
    self.evaluation = evaluation

  def evaluate(self, graph):
    return self.evaluation(graph)


class GraphPoint(O):
  def __init__(self, graph):
    """
    Point used for modelling. More so an instance of model.
    Decisions are graph and objectives can be set
    :param graph: a networkx graph
    """
    O.__init__(self)
    self.decisions = graph
    self.objectives = None
    # Attributes for NSGA2
    self.dominating = 0
    self.dominated = []
    self.crowd_dist = 0

  @staticmethod
  def evaluate_length(graph):
    return nx.dag_longest_path_length(graph)

  @staticmethod
  def evaluate_degree(graph):
    return nx.average_node_connectivity(graph)

  def __hash__(self):
    return hash(self.decisions)

  def evaluate(self, model):
    try:
      if not self.objectives:
        self.objectives = {name: obj.evaluate(self.decisions) for name, obj in model.objectives.items()}
      return self.objectives
    except nx.NetworkXException as e:
      print("EXCEPTION : \n%s" % e)
      model.draw(self)
      exit()
