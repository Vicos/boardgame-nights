from peewee import *

# BoardGameGeek Model
database = SqliteDatabase(':memory:')

ANONYMOUS_PLAYER_NAME = 'John Doe'

class BaseModel(Model):
  class Meta:
    database = database

class Game(BaseModel):
  gameid = IntegerField(primary_key=True)
  name = CharField()
  def byPlays(self):
    return ( Game
              .select()
              .join(Play)
              .group_by(Game.gameid)
              .order_by(fn.Count(Play.playid).desc()) )

class Play(BaseModel):
  playid = IntegerField(primary_key=True)
  date = DateField(null=True)
  location = CharField(null=True)
  quantity = IntegerField(null=True)
  length = IntegerField(null=True)
  game = ForeignKeyField(Game, related_name='plays', null=True)

class Player(BaseModel):
  name = CharField(primary_key=True)
  def byPlays(self):
    return ( Player
              .select()
              .join(PlayerPlay)
              .group_by(Player.name)
              .order_by(fn.Count(PlayerPlay.play).desc()) )
  def wins(self):
    return (self.plays.where(PlayerPlay.win == True))
  def defeats(self):
    return (self.plays.where(PlayerPlay.win == False))
  def ratio(self):
    return ((1.0 * self.wins().count() / self.defeats().count()) if (self.defeats().count() > 0) else None)

class PlayerPlay(BaseModel):
  play = ForeignKeyField(Play, related_name='players')
  player = ForeignKeyField(Player, related_name='plays', null=True)
  win = BooleanField(null=True)
  score = IntegerField(null=True)
  startposition = IntegerField(null=True)
  new = BooleanField(null=True)
  color = CharField(null=True)

# start a permanent connection
database.connect()
# in-memory database always need to create tables
database.create_tables([Game, Play, Player, PlayerPlay])

# BoardGameGeek Fetcher

import logging
import requests
import json
from xml.etree import ElementTree

BGG_PLAYS_URL = 'http://boardgamegeek.com/xmlapi2/plays'
BGG_MAX_PLAY_PER_REQUEST = 100

class Fetcher:
  def fetch(self):
    """
      Fetch BGG to get all plays of a specific account
    """
    isEndOfList = False
    page = 1
    while not isEndOfList:
      logging.info("Fetching BGG plays (page %d)" % ( page ))
      r = requests.get(url=BGG_PLAYS_URL,
        params={
          'username': 'leochab',
          'page': page,
          'type': 'thing',
          'subtype': 'boardgame'
        })
      isEndOfList = self.parse( r.text.encode('utf8') )
      page += 1

  def openSample(self, filename):
    """
      Open a sample and parse it.
      Designed for testing purpose.
    """
    import os.path as path
    logging.info("Parsing sample '%s'" % ( filename ))
    filepath = path.join(path.dirname(path.realpath(__file__)), filename)
    with open(filepath, 'r') as f:
      self.parse( f.read() )

  def parse(self, xml):
    """
      Parse the BGG reply, in XML string
      Return True when the last play has been founded
    """
    root = ElementTree.fromstring(xml)
    assert (root.tag == 'plays')
    for playElement in root:
      self._parsePlay( playElement )
    return ( len(root) != BGG_MAX_PLAY_PER_REQUEST )

  def _parsePlay(self, element):
    assert (element.tag == 'play')
    # create model instance
    playid = int( element.get('id') )
    p = Play.create(playid=playid)
    # and fill it
    if element.get('date'):
      p.date = element.get('date')
    if element.get('location'):
      p.location = element.get('location')
    try:
      p.quantity = int( element.get('quantity') )
    except:
      pass
    try:
      p.length = int( element.get('length') )
    except:
      pass
    p.save()
    # parse children
    g = self._parseGame( element.find('item') )
    p.game = g
    p.save()
    self._parsePlayers( element.find('players'), p )

  def _parseGame(self, element):
    assert (element.tag == 'item')
    gameid = int( element.get('objectid') )
    (g, _) = Game.get_or_create(
      gameid=gameid, defaults={'name': element.get('name')})
    return ( g )

  def _parsePlayers(self, element, play):
    assert (element.tag == 'players')
    for playerElement in element:
      self._parsePlayer(playerElement, play)

  def _parsePlayer(self, element, play):
    assert (element.tag == 'player')
    # instanciate the player and player-play association
    name = element.get('name') if element.get('name') else ANONYMOUS_PLAYER_NAME
    (player, _) = Player.get_or_create(name=name)
    pp = PlayerPlay(play=play, player=player)
    # fill the association
    if element.get('color'):
      pp.color = element.get('color')
    # parse integer values
    try:
      pp.startposition = int( element.get('startposition') )
    except:
      pass
    try:
      pp.score = int( element.get('score') )
    except:
      pass
    pp.new = ( element.get('new') == "1" )
    pp.win = ( element.get('win') == "1" )
    # save changes
    pp.save()

# Cactus Plugin API

def preBuild(site):
  f = Fetcher() 
  # f.fetch() # only for prod purpose
  f.openSample('test-samples.xml') # only for testing purpose

def preBuildPage(site, page, context, data):
  context['Play'] = Play
  context['Game'] = Game
  context['Player'] = Player
  context['PlayerPlay'] = PlayerPlay
  return context, data
