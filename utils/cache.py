from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
from utils.lib import mkdir
import cPickle as cPkl


def load_file(file_name):
  with open(file_name) as f:
    return cPkl.load(f)


def save_file(file_name, obj):
  directory = file_name.rsplit("/", 1)[0]
  mkdir(directory)
  with open(file_name, "wb") as f:
    cPkl.dump(obj, f, cPkl.HIGHEST_PROTOCOL)
