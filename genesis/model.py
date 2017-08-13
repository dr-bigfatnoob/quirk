from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

import re
import pydot as dot
import networkx as nx
import random
from collections import OrderedDict
from utils import lib
from utils.lib import O
from genesis.gen_utils import GraphPoint, Objective


__author__ = "bigfatnoob"


MODEL_SETTINGS = O(
  objs={obj.name: obj for obj in [
    Objective("length", lib.MINIMIZE, GraphPoint.evaluate_length),
    Objective("degree", lib.MINIMIZE, GraphPoint.evaluate_degree),
  ]}
)


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


class Model(O):
  def __init__(self, vocab=None, positives=None, negatives=None):
    O.__init__(self)
    self.vocabulary = Vocabulary() if not vocab else vocab
    self.positives = set()
    self.negatives = set()
    if positives: self.add_examples(positives, is_positive=True)
    if negatives: self.add_examples(negatives, is_positive=False)
    self.objectives = MODEL_SETTINGS.objs

  def add_examples(self, examples, is_positive=True):
    for example in examples:
      self.vocabulary.update_node(example.source)
      self.vocabulary.update_edge(example.relation)
      self.vocabulary.update_node(example.target)
      if is_positive:
        self.positives.add(example)
      else:
        self.negatives.add(example)

  @staticmethod
  def _cycle_exists(graph):
    try:
      # return len(nx.find_cycle(graph, graph.nodes())) > 0
      return len(list(nx.simple_cycles(graph))) > 0
    except nx.exception.NetworkXNoCycle:
      return False

  def _create_edge(self, graph, existing):
    stmt = None
    while stmt is None or str(stmt) in existing:
      target = choice(self.vocabulary.nodes)
      in_edges = graph.in_edges([target], data=True)
      if in_edges:
        relations = set([edge[2]['relation'] for edge in in_edges])
        assert len(relations) == 1, "Multiple incoming relations to node %s" % target
        relation = choice(relations)
      else:
        relation = choice(self.vocabulary.edges)
      source = target
      while source == target:
        source = choice(self.vocabulary.nodes)
      # Checking if edge or its reverse does not exist in graph
      if graph.has_edge(source, target) or graph.has_edge(target, source):
        stmt = None
      else:
        stmt = Statement(source, relation, target)
    graph.add_edge(stmt.source, stmt.target, relation=stmt.relation)
    if not self._cycle_exists(graph):
      existing.add(stmt)
    else:
      graph.remove_edge(stmt.source, stmt.target)
    return graph, existing

  def evaluate_constraints(self, solution):
    """
    :param solution: Instance of graph
    :return:
    """
    return not self._cycle_exists(solution), 0

  def generate(self):
    graph = nx.DiGraph()
    graph.add_nodes_from(self.vocabulary.nodes)
    for stmt in self.positives:
      graph.add_edge(stmt.source, stmt.target, relation=stmt.relation)
    existing = set([str(stmt) for stmt in self.positives] + [str(stmt) for stmt in self.negatives])
    existing.update()
    while not nx.is_weakly_connected(graph):
      graph, existing = self._create_edge(graph, existing)
    return GraphPoint(graph)

  def populate(self, size):
    population = set()
    while len(population) < size:
      point = self.generate()
      if not self._cycle_exists(point.decisions):
       population.add(self.generate())
    return list(population)

  def bdom(self, obj1, obj2):
    """
    Binary Domination
    :param obj1: Objective 1
    :param obj2: Objective 2
    :return: Check objective 1 dominates objective 2
    """
    at_least = False
    for i in self.objectives.keys():
      a, b = obj1[i], obj2[i]
      if self.objectives[i].direction.better(a, b):
        at_least = True
      elif a == b:
        continue
      else:
        return False
    return at_least

  def better(self, obj1, obj2):
    if self.bdom(obj1, obj2):
      return 1
    elif self.bdom(obj2, obj1):
      return 2
    return 0

  def draw(self, point, fig_name="genesis/temp.png"):
    dot_graph = dot.Dot(graph_type='digraph', rankdir="BT")
    for node in self.vocabulary.nodes:
      dot_graph.add_node(dot.Node(name=node))
    for edge in point.decisions.edges(data=True):
      style = 'dashed' if edge[2]['relation'] == 'or' else 'solid'
      dot_graph.add_edge(dot.Edge(edge[0], edge[1], style=style))
    dot_graph.write(fig_name, format='png')


def test_basic():
  pos_examples = ["c1 -> or -> cost",
                  "b1 -> or -> benefit",
                  ]
  neg_examples = ["c1 -> and -> b1",
                  "c1 -> or -> b1"]
  other_nodes = {"c2", "nb"}
  other_edges = {"and"}
  vocab = Vocabulary(other_nodes, other_edges)
  pos_examples = map(Statement.from_string, pos_examples)
  neg_examples = map(Statement.from_string, neg_examples)
  model = Model(vocab, pos_examples, neg_examples)
  pop = model.populate(5)
  print([p.evaluate(model) for p in pop])
  model.draw(pop[0], "genesis/temp0.png")
  model.draw(pop[4], "genesis/temp4.png")


def test_nsga():
  from technix import nsga
  pos_examples = ["c1 -> or -> cost",
                  "b1 -> or -> benefit",
                  ]
  neg_examples = ["c1 -> and -> b1",
                  "c1 -> or -> b1"]
  other_nodes = {"c2", "nb"}
  other_edges = {"and"}
  vocab = Vocabulary(other_nodes, other_edges)
  pos_examples = map(Statement.from_string, pos_examples)
  neg_examples = map(Statement.from_string, neg_examples)
  model = Model(vocab, pos_examples, neg_examples)
  pop = model.populate(100)
  # print([p.evaluate(model) for p in pop])
  pop = nsga.select(model, pop, len(pop))
  model.draw(pop[0], "genesis/temp_best.png")
  model.draw(pop[-1], "genesis/temp_last.png")


# TODO 1: Check optimization
# TODO 2: Check best query generation


if __name__ == "__main__":
  test_nsga()
