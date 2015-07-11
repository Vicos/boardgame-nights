import logging
import requests
import json
from xml.etree import ElementTree

from bggmodels import Play, Game, Player, PlayerPlay

BGG_PLAYS_URL = 'http://boardgamegeek.com/xmlapi2/plays'
BGG_MAX_PLAY_PER_REQUEST = 100
ANONYMOUS_PLAYER_NAME = 'John Doe'

class Fetcher:
  def fetch(self, username):
    """
      Fetch BGG to get all plays of a specific account
    """
    isEndOfList = False
    page = 1
    while not isEndOfList:
      logging.info("Fetching BGG plays (user: %s, page: %d)" % ( username, page ))
      r = requests.get(url=BGG_PLAYS_URL,
        params={
          'username': username,
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
