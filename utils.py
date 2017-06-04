from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
import numpy as np

__author__ = "bigfatnoob"


def gt(a, b):
  """
  True if a > b
  :param a:
  :param b:
  :return:
  """
  return a > b

def lt(a, b):
  """
  True if a < b
  :param a:
  :param b:
  :return:
  """
  return a < b

def gte(a, b):
  """
  True if a >= b
  :param a:
  :param b:
  :return:
  """
  return a >= b

def lte(a, b):
  """
  True if a <= b
  :param a:
  :param b:
  :return:
  """
  return a <= b

def eq(a, b):
  """
  True if a == b
  :param a:
  :param b:
  :return:
  """
  return a == b

def neq(a, b):
  """
  True if a != b
  :param a:
  :param b:
  :return:
  """
  return a != b

def np_to_list(a):
  """
  Convert numpy list to python list
  :param a: instance of numpy array
  :return:
  """
  return np.asarray(a, dtype=float).tolist()


class O:
  def __init__(self,**d): self.has().update(**d)
  def has(self): return self.__dict__
  def update(self,**d): self.has().update(d); return self
  def __repr__(self)   :
    def _name(val):
      if isinstance(val, list):
        return [_name(v) for v in val]
      if hasattr(val, '__call__'):
        return val.__name__
      return val
    show=[':%s %s' % (k,_name(self.has()[k]))
      for k in sorted(self.has().keys() )
      if k[0] is not "_"]
    txt = ' '.join(show)
    if len(txt) > 60:
      show=map(lambda x: '\t'+x+'\n',show)
    return '{'+' '.join(show)+'}'
  def __getitem__(self, item):
    return self.has().get(item)
  def clone(self):
    cloned = O()
    for key, val in self.has().iteritems():
      cloned.__dict__[key] = val
    return cloned


class Direction(O):
  def __init__(self, name, better, worse):
    self.name = name
    self.better = better
    self.worse = worse
    O.__init__(self)


MINIMIZE = Direction("min", lt, gte)
MAXIMIZE = Direction("max", gt, lte)
