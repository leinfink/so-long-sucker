from enum import Enum
from collections import Counter

import random

import django.dispatch

import pickle
import redis

from django.conf import settings

game_state_changed_signal = django.dispatch.Signal()
concurrent_action_signal = django.dispatch.Signal()
game_action_signal = django.dispatch.Signal()

class GameState(Enum):
    NOT_RUNNING = 0 #
    FINISHED = 1 #
    ABORTED = 2 #
    AWAIT_MOVE = 3 #
    AWAIT_GIVE_MOVE = 4 #
    AWAIT_CHOOSE_KILL = 5 #
    AWAIT_REFUSALS = 6

class GameAction(Enum):
    REFUSE_HELP = 0 
    PLAY_MOVE = 1 #
    KILL_FROM_CAPTURE = 2 #
    KILL_PRISONER = 3
    TRANSFER = 4 #
    GIVE_MOVE = 5 #
    PILE_CREATED = 6
    PLAYER_KILLED = 7
    ENTIRE_PILE_KILLED = 8

def determine_starting_chips(player_count):
    if player_count <= 4:
        return 7
    elif player_count == 5:
        return 6
    elif player_count == 6:
        return 5
    elif player_count == 7:
        return 4
    elif player_count == 8:
        return 4
    else:
        return 3

class GameRun:
    
    def choose_starting_player(players):
        random.seed()
        i = random.randint(0, len(players)-1)
        starting_player = players[i]
        return starting_player

    def possible_moves(alive_player_colors, played_pile):
        non_contained = []
        for c in alive_player_colors:
            if c not in played_pile:
                non_contained.append(c)
        if non_contained:
            return non_contained
        else:
            highest_position = [0] * len(alive_player_colors)
            for p in alive_player_colors:
                for i, color in enumerate(reversed(played_pile)):
                    if color == p:
                        highest_position[p] = i
                        break
            return [highest_position.index(max(highest_position))]
    
    def __init__(self, game):
        self.db_game = game # models.Game
        self.players = []
        self.player_count = len(game.players.all())
        self.winner = None
        self.starting_chips = determine_starting_chips(self.player_count)
       
        for p in game.players.all():
            new_player = GamePlayer(p.username,
                                    self.player_count,
                                    self.starting_chips,
                                    len(self.players))
            self.players.append(new_player)
        self.state = GameState.NOT_RUNNING

    def start(self):
        self.current_player = GameRun.choose_starting_player(self.players)
        self.last_players = [None]*self.player_count
        self.playing_area = [] # a list of ordered list (= piles)
        self.dead_box = []
        self.set_state(GameState.AWAIT_MOVE)
        return self.state

    def get_living_players(self):
        return list(filter(lambda p: p.alive, self.players))
        
    def get_living_colors(self):
        colors = []
        for p in self.players:
            if p.alive:
                colors.append(p.color)
        return colors

    def set_current_player(self, p):
        if not p.alive:
            return False
        self.last_players = self.last_players[1:] + [self.current_player]
        self.current_player = p
        return self.current_player
       
    def set_current_player_to_last_available(self):
        for p in reversed(self.last_players):
            if p.alive:
                self.set_current_player(p)
                break
        return self.current_player
    
    def print_current_state(self):
        player_names = []
        player_states = []
        for p in self.players:
            player_names.append(str(p))
            player_states.append(
                '---\n'
                'Player ' + str(p) + ':\n'
                'Stock count: ' + str(p.stock) + '\n'
                'Prisoners: ' + str(p.prisoners) + '\n'
            )
        output = (
            '--- Current game state ---\n'
            'Game state: ' + str(self.state) + '\n'
            'Players: ' + str(player_names) + '\n'
            'Current player: ' + str(self.current_player) + '\n'
            'Playing area: ' + str(self.playing_area) + '\n'
            'Dead box: ' + str(self.dead_box) + '\n'
            )
        output = output + ''.join(player_states)
        output = output + '--- End of game state output ---'
        return output

    def redis_save(self):
        if settings.REDIS_UNIX:
            r = redis.Redis(unix_socket_path=settings.REDIS_UNIX_PATH, db=0)
        else:
            r = redis.Redis(host=settings.REDIS_HOST, port=6379, db=0)
            
        p = r.pipeline()
        key = 'game_' + str(self.db_game.pk)
        p.watch(key)
        p.multi()
        pickled_object = pickle.dumps(self)
        p.set(key, pickled_object)
        p.execute()

    def set_state(self, state):
        available_player_targets = None
        captured_pile = None
        captured_pile_num = None
        winner = None
        
        if state == GameState.AWAIT_MOVE:
            if not self.current_player.has_chips():
                state = GameState.AWAIT_REFUSALS
                self.refused = []
        elif state == GameState.AWAIT_GIVE_MOVE:
            available_colors = GameRun.possible_moves(
                self.get_living_colors(),
                self.playing_area[self.last_played_pile]
            )
            available_player_targets = [self.players[p] for p in available_colors]
        elif state == GameState.AWAIT_CHOOSE_KILL:
            captured_pile = self.playing_area[self.last_played_pile]
            captured_pile_num = self.last_played_pile
        elif state == GameState.FINISHED:
            winner = self.winner
            
                
        self.state = state
        # print(self.print_current_state())
        self.redis_save()

        game_state_changed_signal.send_robust(
            sender=GameRun.__class__,
            game=self.db_game,
            new_state=self.state,
            current_player=self.current_player,
            available_player_targets=available_player_targets,
            captured_pile=captured_pile,
            captured_pile_num=captured_pile_num,
            winner=winner,
            alive=self.get_living_players(),
        )
        
        return(self.state)

    def refuse_help(self, player):
        if (self.state == GameState.AWAIT_REFUSALS and
            player != self.current_player and
            player.alive and
            player not in self.refused):
            # accept refusal
            self.refused.append(player)
            if len(self.refused) == len(self.get_living_players())-1:
                self.mark_defeated(self.current_player)
            else:
                self.redis_save()
            game_action_signal.send(sender=GameRun.__class__,
                                    game=self.db_game,
                                    action_type=GameAction.REFUSE_HELP,
                                    acting_player=player.playername,
                                    target=self.current_player.playername,
                                    used_color=None)
            return True
        else:
            return None

    def mark_defeated(self, player):
        if (self.state == GameState.AWAIT_REFUSALS and
            self.current_player == player):
            # sadly, he died
            player.kill()
            game_action_signal.send(sender=GameRun.__class__,
                                    game=self.db_game,
                                    action_type=GameAction.PLAYER_KILLED,
                                    acting_player=player.playername,
                                    target=None,
                                    used_color=None)
            if len(self.get_living_players()) == 1:
                self.mark_winner(self.get_living_players()[0])
                return player
            self.set_current_player_to_last_available()
            self.set_state(GameState.AWAIT_MOVE)
            return player
        else:
            return None

    def mark_winner(self, player):
        self.winner = player
        self.set_state(GameState.FINISHED)
        return player
        
    def transfer(self, playerA, playerB, color):
        if (playerA.prisoners[color] > 0 and 
            playerA.color != color and # just a double-check
            playerA.alive and
            playerB.alive and
            playerA is not playerB):
            # allow transfer
            playerA.prisoners[color] -= 1
            if color == playerB.color:
                playerB.stock += 1
            else:
                playerB.prisoners[color] += 1
            self.redis_save()
            game_action_signal.send(sender=GameRun.__class__,
                                    game=self.db_game,
                                    action_type=GameAction.TRANSFER,
                                    acting_player=playerA.playername,
                                    target=playerB.playername,
                                    used_color=color)
                
            if (self.state == GameState.AWAIT_REFUSALS and
                self.current_player == playerB):
                # player was rescued!
                self.set_state(GameState.AWAIT_MOVE)
            return color
        else:
            return None
        
    def is_capture(played_pile):
        if len(played_pile)>1:
            return played_pile[-1] == played_pile[-2]
        else:
            return False
    
    def play_move(self, player, pile, color):
        if (self.state == GameState.AWAIT_MOVE and
            self.current_player == player and
            player.alive and
            player.can_play_color(color)):
            # allow move
            if player.color == color:
                player.stock -= 1 # own chip
            else:
                player.prisoners[color] -= 1 # foreign chip
                
            if 0 <= pile <= (len(self.playing_area)-1):
                self.playing_area[pile].append(color)
                self.last_played_pile = pile
            else:
                new_pile = []
                new_pile.append(color)
                self.playing_area.append(new_pile)
                self.last_played_pile = len(self.playing_area)-1
                target = self.last_played_pile + 1
                game_action_signal.send(sender=GameRun.__class__,
                                        game=self.db_game,
                                        action_type=GameAction.PILE_CREATED,
                                        acting_player=player.playername,
                                        target=target,
                                        used_color=color)
            self.redis_save()
            game_action_signal.send(sender=GameRun.__class__,
                                    game=self.db_game,
                                    action_type=GameAction.PLAY_MOVE,
                                    acting_player=player.playername,
                                    target=self.last_played_pile,
                                    used_color=color)

            if GameRun.is_capture(self.playing_area[self.last_played_pile]):
                if not self.players[color].alive:
                    # remove from playing area and add to dead box
                    for c in self.playing_area[self.last_played_pile]:
                        self.dead_box.append(c)
                        
                    game_action_signal.send(sender=GameRun.__class__,
                                            game=self.db_game,
                                            action_type=GameAction.ENTIRE_PILE_KILLED,
                                            acting_player=player.playername,
                                            target=None,
                                            used_color=None,
                                            captured_pile=self.playing_area[self.last_played_pile],
                                            captured_pile_num=self.last_played_pile)
                    
                    self.playing_area[self.last_played_pile] = []
                    self.set_current_player_to_last_available()                   
                    self.set_state(GameState.AWAIT_MOVE)
                else:
                    self.pile_to_kill = self.playing_area[self.last_played_pile]
                    captured_color = self.pile_to_kill[-1]
                    self.set_current_player(self.players[captured_color])
                    self.set_state(GameState.AWAIT_CHOOSE_KILL)
            else:
                return self.set_state(GameState.AWAIT_GIVE_MOVE)
        else:
            return None

    
    def kill_from_capture(self, player, color):
        color = int(color)
        if (self.state == GameState.AWAIT_CHOOSE_KILL and
            self.current_player.playername == player.playername and
            color in self.pile_to_kill):
            # allow killing, take the rest
            counts = Counter(self.pile_to_kill)
            counts[color] -= 1
            self.dead_box.append(color)
            for key, value in counts.items():
                if key == player.color:
                    player.stock += value
                else:
                    player.prisoners[key] += value
            self.playing_area[self.last_played_pile] = []
            self.redis_save()
            game_action_signal.send(sender=GameRun.__class__,
                                    game=self.db_game,
                                    action_type=GameAction.KILL_FROM_CAPTURE,
                                    acting_player=player.playername,
                                    target=None,
                                    used_color=color,
                                    captured_pile=self.pile_to_kill,
                                    captured_pile_num=self.last_played_pile)
            return self.set_state(GameState.AWAIT_MOVE)
        else:
            return None
                
    def kill_from_prisoners(self, player, color):
        color = int(color)
        if (player.alive and
            color != player.color and
            player.prisoners[color] >= 1):
            # allow killing
            player.prisoners[color] -= 1
            self.dead_box.append(color)

            self.redis_save()
            game_action_signal.send(sender=GameRun.__class__,
                                    game=self.db_game,
                                    action_type=GameAction.KILL_PRISONER,
                                    acting_player=player.playername,
                                    target=None,
                                    used_color=color)
            return color
        else:
            return None

    def give_move(self, playerA, playerB):
        if (self.state == GameState.AWAIT_GIVE_MOVE and
            self.current_player == playerA and
            playerA.alive and
            playerB.alive and
            playerB.color in GameRun.possible_moves(
                self.get_living_colors(),
                self.playing_area[self.last_played_pile])
            ):
            # allow giving move
            self.set_current_player(playerB)
            self.set_state(GameState.AWAIT_MOVE)
        else:
            return None

class GamePlayer:
    def __init__(self, playername, total_player_count, starting_chips, color):
        self.playername = playername
        self.color = color
        self.stock = starting_chips # count of own chips in possession
        
        self.prisoners = [0]*total_player_count
        
        # prisoners: a list of length player_count with counts of
        # captured chips. this should actually be (player_count-1),
        # because you can't hold your own chips as prisoners, but for
        # simplicity we keep it in and just make sure you can never
        # imprison your own chips.
        
        self.alive = True

    def has_chips(self):
        return ((self.stock > 0) or (sum(self.prisoners) > 0))

    def can_play_color(self, color):
        if self.prisoners[color] >= 1 and self.color != color:
            return True
        elif self.stock >= 1 and self.color == color:
            return True
        else:
            return False
        
    def kill(self):
        self.alive = False
        
    def __str__(self):
        return self.playername
