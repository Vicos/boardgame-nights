from peewee import *

database = SqliteDatabase(':memory:')

class BaseModel(Model):
  class Meta:
    database = database

class Game(BaseModel):
  gameid = IntegerField(primary_key=True)
  name = CharField()

  @property
  def count(self):
      return self.Play.count()
  @property
  def lastplayed(self):
    return ( self.Play.order_by(Play.date.desc())[0].date )

class Play(BaseModel):
  playid = IntegerField(primary_key=True)
  date = DateField(null=True)
  location = CharField(null=True)
  quantity = IntegerField(null=True)
  length = IntegerField(null=True)
  game = ForeignKeyField(Game, related_name='Play', null=True)

class Player(BaseModel):
  name = CharField(primary_key=True)

  @property
  def plays(self):
    return ( sum([pp.play.quantity for pp in self.PlayerPlay]) )
  @property
  def wins(self):
    return (self.PlayerPlay.where(PlayerPlay.win == True).count())
  @property
  def defeats(self):
    return (self.PlayerPlay.where(PlayerPlay.win == False).count())
  @property
  def ratio(self):
    return ((1.0 * self.wins / self.defeats) if (self.defeats > 0) else None)

class PlayerPlay(BaseModel):
  play = ForeignKeyField(Play, related_name='PlayerPlay')
  player = ForeignKeyField(Player, related_name='PlayerPlay', null=True)
  win = BooleanField(null=True)
  score = IntegerField(null=True)
  startposition = IntegerField(null=True)
  new = BooleanField(null=True)
  color = CharField(null=True)

# start a permanent connection
database.connect()
# in-memory database always need to create tables
database.create_tables([Game, Play, Player, PlayerPlay])
