from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

from utils.lib import O
import re
import pydot as dot
import networkx as nx
import random

__author__ = "bigfatnoob"


def choice(seq):
  if not seq:
    return None
  return random.sample(seq, 1)[0]


class Statement(O):
  Pattern = r'(\s*\w[\w\s\-]*)->(\s*\w[\w\s\-]*)->(\s*\w[\w\s\-]*)'

  def __init__(self, source, relation, target):
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
  def __init__(self, graph):
    O.__init__(self)
    self.decisions = graph
    self.objectives = None

  def __hash__(self):
    return hash(self.decisions)


class Model(O):
  def __init__(self, vocab=None, positives=None, negatives=None):
    O.__init__(self)
    self.vocabulary = Vocabulary() if not vocab else vocab
    self.positives = set()
    self.negatives = set()
    if positives: self.add_examples(positives, is_positive=True)
    if negatives: self.add_examples(negatives, is_positive=False)

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
      nx.find_cycle(graph)
    except nx.exception.NetworkXNoCycle:
      return False
    return True

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
    existing = set([str(stmt) for stmt in self.positives])
    existing.update([str(stmt) for stmt in self.negatives])
    while not nx.is_weakly_connected(graph):
      graph, existing = self._create_edge(graph, existing)
    return GraphPoint(graph)

  def populate(self, size):
    population = set()
    while len(population) < size:
      population.add(self.generate())
    return list(population)

  def draw(self, point, fig_name="genesis/temp.png"):
    dot_graph = dot.Dot(graph_type='digraph', rankdir="BT")
    for node in self.vocabulary.nodes:
      dot_graph.add_node(dot.Node(name=node))
    for edge in point.decisions.edges(data=True):
      style = 'dashed' if edge[2]['relation'] == 'or' else 'solid'
      dot_graph.add_edge(dot.Edge(edge[0], edge[1], style=style))
    dot_graph.write(fig_name, format='png')


def draw(statements, file_name):
  graph = dot.Dot(graph_type='digraph', rankdir="BT")
  for stmt in statements:
    style = 'dashed' if stmt.relation == 'or' else 'solid'
    graph.add_edge(dot.Edge(stmt.source, stmt.target, style=style))
  graph.write(file_name, format='png')


def test():
  # TODO 1) Come up with objectives
  # TODO 2) Verify nsga 2.

  pos_examples = ["c1 -> or -> cost",
                  # "c2 -> or -> cost",
                  "b1 -> or -> benefit",
                  # "b2 -> or -> benefit",
                  # "cost -> and -> nb",
                  # "benefit -> and -> nb"
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
  model.draw(pop[0], "genesis/temp0.png")
  model.draw(pop[4], "genesis/temp4.png")


if __name__ == "__main__":
  test()
