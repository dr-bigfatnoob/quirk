from __future__ import print_function, division
import sys
import os

sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

import networkx as nx
from utils.lib import O
import random
import re

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


def choice(seq):
  if not seq:
    return None
  return random.sample(seq, 1)[0]


class Statement(O):
  Pattern = r'(\s*\w[\w\s\-]*)->(\s*\w[\w\s\-]*)->(\s*\w[\w\s\-]*)'

  def __init__(self, source, relation, target):
    """
    source -> relation -> target
    :param source: Source Node
    :param relation: Relation between source and target
    :param target: Target Node
    """
    O.__init__(self)
    self.source = source.strip()
    self.relation = relation.strip()
    self.target = target.strip()

  @staticmethod
  def from_string(stmt):
    groups = re.match(Statement.Pattern, stmt).groups()
    if len(groups) == 3:
      return Statement(*groups)
    raise Exception("Invalid format: %s. \nLegal format: %s" % (stmt, "Source->Relation->Target"))

  def __repr__(self):
    return "%s -> %s -> %s" % (self.source, self.relation, self.target)

  def __hash__(self):
    return hash("%s;%s;%s" % (self.source, self.relation, self.target))

  def __eq__(self, other):
    if not other:
      return False
    return hash(self) == hash(other)


class Vocabulary(O):
  def __init__(self, nodes=None, edges=None):
    """
    Vocabulary of the graph
    :param nodes: Set of all possible nodes
    :param edges: Set of all possible edges
    """
    O.__init__(self)
    self.nodes = set() if not nodes else nodes
    self.edges = set() if not edges else edges

  def add_stmt(self, stmt):
    self.update_node(stmt.source)
    self.update_edge(stmt.relation)
    self.update_node(stmt.target)

  def update_node(self, node):
    self.nodes.add(node)

  def update_edge(self, edge):
    self.edges.add(edge)


class GraphPoint(O):
  def __init__(self, graph, statements):
    """
    Point used for modelling. More so an instance of model.
    Decisions are graph and objectives can be set
    :param graph: a networkx graph
    """
    O.__init__(self)
    self.decisions = graph
    self.statements = statements
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

  def __eq__(self, other):
    if other is None:
      return False
    diff = nx.difference(self.decisions, other.decisions)
    return len(diff.edges()) == 0

  def evaluate(self, model):
    try:
      if not self.objectives:
        self.objectives = {name: obj.evaluate(self.decisions) for name, obj in model.objectives.items()}
      return self.objectives
    except nx.NetworkXException as e:
      print("EXCEPTION : \n%s" % e)
      model.draw(self.decisions)
      exit()

  def clone(self):
    return GraphPoint(self.decisions.copy(), set(list(self.statements)[:]))
