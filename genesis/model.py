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
    return hash(repr(self))


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
  def __init__(self, decisions):
    O.__init__(self)
    self.decisions = decisions
    self.objectives = None


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
    while stmt is None or stmt in existing:
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
      stmt = Statement(source, relation, target)
    graph.add_edge(stmt.source, stmt.target, relation=stmt.relation)
    if not self._cycle_exists(graph):
      existing.add(stmt)
    else:
      graph.remove_edge(stmt.source, stmt.target)

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
    existing = set(self.positives)
    existing.update(self.negatives)
    while not nx.is_weakly_connected(graph):
      self._create_edge(graph, existing)
    return GraphPoint(graph)

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
  pos_examples = ["c1 -> or -> cost",
                  # "c2 -> or -> cost",
                  "b1 -> or -> benefit",
                  # "b2 -> or -> benefit",
                  # "cost -> and -> nb",
                  # "benefit -> and -> nb"
                  ]
  other_nodes = {"c2", "nb"}
  other_edges = {"and"}
  vocab = Vocabulary(other_nodes, other_edges)
  pos_examples = map(Statement.from_string, pos_examples)
  model = Model(vocab, pos_examples)
  point = model.generate()
  model.draw(point)
  # draw(pos_examples, "genesis/temp.png")

if __name__ == "__main__":
  test()
