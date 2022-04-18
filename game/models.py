from django.db import models

from django.contrib.auth import get_user_model

from datetime import datetime

from .game_logic import GameRun

import django.dispatch

import redis

from django.conf import settings

game_started_signal = django.dispatch.Signal()

def get_deleted_user():
    return get_user_model().objects.get_or_create(username='deleted')[0]

def get_anonymous_user():
    return get_user_model().objects.get_or_create(username='anonymous')[0]

class Game(models.Model):
    creator = models.ForeignKey(get_user_model(),
                                on_delete=models.SET(get_deleted_user),
                                related_name='creator')
    
    players = models.ManyToManyField(get_user_model(),
                                     through='Player')

    winner = models.ForeignKey(get_user_model(),
                               on_delete=models.SET(get_deleted_user),
                               related_name='winner',
                               null=True,
                               blank=True
                               )
    # dates
    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(null=True, blank=True)
    completed = models.DateTimeField(null=True, blank=True)
    modified = models.DateTimeField(auto_now=True)

    finalGameState = models.BinaryField(null=True, blank=True)

    class Meta:
        get_latest_by = "modified"
        ordering = ["-modified"]

    def __str__(self):
        return 'Game #{0}'.format(self.pk)

    @staticmethod
    def get_total_number_of_games():
        return Game.objects.count()
    
    @staticmethod
    def get_open_games():
        return Game.objects.filter(started=None, completed=None)

    @staticmethod
    def get_open_games_not_joined_by_user(user):
        return filter(lambda x: not x.is_user_a_player(user), Game.get_open_games())
 
    @staticmethod
    def created_count(user):
        return Game.objects.filter(creator=user).count()
 
    @staticmethod
    def get_games_for_player(user):
        if not user.is_authenticated:
            return []
        from django.db.models import Q
        return Game.objects.filter(Q(players=user) & Q(completed=None))
 
    @staticmethod
    def get_by_id(id):
        try:
            return Game.objects.get(pk=id)
        except Game.DoesNotExist:
            pass
        
    @staticmethod
    def create_new(user):
        """
        Create a new game
        :param user: the user that created the game
        :return: a new game object
        """
        if not user.is_authenticated:
            user = get_anonymous_user()
        new_game = Game.objects.create(creator=user)
        new_player = Player(user=user, game=new_game, color=0)
        new_player.save()
        return new_game

    def player_join(self, user):
        if not user.is_authenticated:
            user = get_anonymous_user()
        new_player = Player(user=user, game=self, color=self.get_player_count())
        new_player.save()
        return new_player

    def get_player_count(self):
        return self.players.all().count()

    def is_user_a_player(self, user):
        return user in self.players.all()

    def start(self):
        self.running_game = GameRun(self)
        self.mark_started()
        self.running_game.start()
    
    def mark_started(self):
        """
        Marks a game as having started
        """
        self.started = datetime.now()
        self.save() 
        game_started_signal.send(sender=Game.__class__,
                                 game=self,
                                 starting_chips=self.running_game.starting_chips)

    def mark_complete(self, winner):
        """
        Sets a game to completed status and records the winner
        """
        if settings.REDIS_UNIX:
            r = redis.Redis(unix_socket_path=settings.REDIS_UNIX_PATH, db=0)
        else:
            r = redis.Redis(host=settings.REDIS_HOST, port=6379, db=0)
            
        p = r.pipeline()
        key = 'game_' + str(self.pk)
        p.watch(key)
        self.finalGameState = p.get(key)
        p.multi()
        p.delete('game_' + str(self.pk))
        p.execute()
        
        for p in self.players.all():
            if p.username == winner.playername:
                self.winner = p
                break
        self.completed = datetime.now()
        self.save()

class Player(models.Model):
    user = models.ForeignKey(get_user_model(),
                             on_delete=models.SET(get_deleted_user),
                             null=True,
                             blank=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    color = models.IntegerField(default=0, unique=False)

    # if we allow anonymous users, we should not make this uniqueness constraint!
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'game'],
                                    name='unique_players_in_game')
        ]
