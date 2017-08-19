from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
from utils.lib import O
from genesis.gen_utils import Statement

__author__ = "bigfatnoob"


class Oracle(O):
  def __init__(self):
    O.__init__(self)

  def validate(self, query):
    raise NotImplemented("Has to be implemented in sub class.")


class StatementOracle(Oracle):

  def __init__(self, statements):
    Oracle.__init__(self)
    self.statements = set()
    for statement in statements:
      if isinstance(statement, str):
        self.statements.add(Statement.from_string(statement))
      else:
        self.statements.add(statement)

  def validate(self, query):
    return query in self.statements
