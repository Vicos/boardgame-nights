# -*- coding: utf-8 -*-

import logging
import os
import shutil
from jinja2 import Environment, PackageLoader

from lib.bggfetcher import Fetcher
from lib.bggmodels import Play, Game, Player, PlayerPlay

class Builder:
  def __init__(self):
    self.templatedir = 'templates'
    self.builddir = 'build'
    self.env = Environment(loader=PackageLoader(__name__, self.templatedir))
    
  def render(self):
    """
      Render all templates and static resources
    """
    for filepath in self.env.list_templates(filter_func=self.filter_ignored_files):
      if self.is_template(filepath):
        self.render_template(filepath)
      else:
        self.copy_static(filepath)

  def is_template(self, filepath):
    """
      Return True when the file is a Jinja template
    """
    (_, ext) = os.path.splitext(filepath)
    return (ext == '.jinja')

  def render_template(self, filepath):
    assert (self.is_template(filepath))
    self.prepare_subdirectories(filepath)
    dst = self.get_template_destination(filepath)
    logging.info("Rendering %s to %s" % (filepath, dst))
    with open(dst, 'w') as f:
      t = self.env.get_template(filepath)
      f.write(t.render().encode('utf8'))

  def copy_static(self, filepath):
    """
      Copy a static file to the build directory
    """
    assert (not self.is_template(filepath))
    self.prepare_subdirectories(filepath)
    src = os.path.join(self.templatedir, filepath)
    dst = self.get_destination(filepath)
    logging.info("Copying %s to %s" % (src, dst))
    shutil.copyfile(src, dst)

  def prepare_subdirectories(self, filepath):
      """
        Create sub-directories in build directory
      """
      path = os.path.dirname(filepath)
      dst_path = os.path.join(self.builddir, path)
      try:
        os.makedirs(dst_path)
      except:
        pass

  def get_template_destination(self, filepath):
    """
      Compute the destination file path of a template
    """
    assert (self.is_template(filepath))
    (root, _) = os.path.splitext(filepath)
    return (self.get_destination(root))

  def get_destination(self, filepath):
    """
      Compute the destination file path of a static file
    """
    return (os.path.join(self.builddir, filepath))

  def filter_ignored_files(self, filepath):
    """
      Filter function to ignore files beginning by '_' (useful for layouts)
    """
    filename = os.path.basename(filepath)
    return (filename[0] != '_')

if __name__ == "__main__":
  logging.basicConfig(format='%(levelname)7s: %(message)s', level=logging.INFO)
  
  import argparse
  parser = argparse.ArgumentParser(description='Build static Web pages of the Boardgame Nights project.')
  parser.add_argument('-f', '--fetch',
                      dest='username',
                      help="fetch USERNAME's plays from boardgamegeek.com")
  args = parser.parse_args()

  # fetch data
  f = Fetcher()
  if args.username:
    f.fetch(username=args.username)
  else:
    f.openSample(filename='test-samples.xml')

  # render pages
  b = Builder()
  b.env.globals = {
      'Play': Play,
      'Game': Game,
      'Player': Player,
      'PlayerPlay': PlayerPlay,
    }
  b.render()
