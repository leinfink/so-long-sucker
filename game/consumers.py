import json
import redis
import pickle

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.template.loader import render_to_string

from config.utils import get_htmx_oob_swap_response
from .models import Game
from .game_logic import GameAction, GameState, concurrent_action_signal
from .views import game as GameView
from game.utils import get_game_through_redis

class LobbyConsumer(WebsocketConsumer):
    
    def connect(self):
        async_to_sync(self.channel_layer.group_add)("lobby", self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)("lobby", self.channel_name)

    def receive(self, text_data):
        pass
    
    def game_created(self, event):
        game =  Game.get_by_id(event['game_id'])
        
        if game.creator != self.scope['user']:
            template = 'game/open_game.html'
            htmx_oob_target = 'afterbegin:#open_games'
        else:
            template = 'game/player_game.html'
            htmx_oob_target = 'afterbegin:#player_games'
            
        data = {
            'user': self.scope['user'],
            'game': game,
        }
        
        output = render_to_string(template, data)
        response = get_htmx_oob_swap_response(output, htmx_oob_target)

        self.send(text_data=response)

    def game_joined(self, event):
        game_id = event['game_id']
        player_count = event['player_count']
        joined_player = event['joined_player']
        
        # send update
        htmx_oob_target =  'innerHTML:#game_' + str(game_id) + ' .player_count'
        response = get_htmx_oob_swap_response(str(player_count),
                                              htmx_oob_target)
        self.send(text_data=response)


        # send notification popup
        popup = render_to_string('game/events/game_joined_notification.html',
                                 {'joined_player': joined_player})
        popup_htmx_oob_target = 'beforeend:#game_' + str(game_id)
        popup_response = get_htmx_oob_swap_response(popup,
                                                    popup_htmx_oob_target)
        self.send(text_data=popup_response)

    def game_started(self, event):
        htmx_oob_target =  'delete:.open_game#game_' + str(event['game_id'])
        response = get_htmx_oob_swap_response('', htmx_oob_target)
        self.send(text_data=response)

        


def get_player_in_gamerun(playername, gameRun):
    player = None
    for p in gameRun.players:
        if p.playername == playername:
            player = p
            break
    return player

class GameConsumer(WebsocketConsumer):
    
    def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = 'game_%s' % self.game_id

        async_to_sync(self.channel_layer.group_add)(self.game_group_name,
                                                    self.channel_name)
        
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.game_group_name,
                                                        self.channel_name)
        
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        
        action = text_data_json['action']
        game_id = text_data_json['game']
        game = Game.get_by_id(game_id)
        
        if action == "join_game":
            return game.player_join(self.scope["user"])
        
        elif action == "start_game":
            return game.start()

        gameRun = get_game_through_redis(game_id)
        player = get_player_in_gamerun(self.scope["user"].username, gameRun)
        
        if action == "give_move":
            targetPlayer = get_player_in_gamerun(text_data_json['move_given'], gameRun)
            gameRun.give_move(player, targetPlayer)
            
        elif action == "chip_put":
            color = text_data_json['chipColor']
            pile = text_data_json['targetPile']
            gameRun.play_move(player, int(pile), int(color))
            
        elif action == "chip_transfer":
            color = text_data_json['chipColor']
            target_player = text_data_json['targetPlayer']
            gameRun.transfer(player, get_player_in_gamerun(target_player,gameRun), int(color))

        elif action == "kill_from_capture":
            color = text_data_json['chipColor']
            gameRun.kill_from_capture(player, color)

        elif action == "prisoner_killed_directly":
            color = text_data_json['chipColor']
            gameRun.kill_from_prisoners(player, color)

        elif action == "refuse_help":
            # print('help refused by someone')
            gameRun.refuse_help(player)

        elif action =="chat_message":
            message = text_data_json['message']
            if message != "":
                concurrent_action_signal.send_robust(
                sender=GameConsumer.__class__,
                    game=game,
                    action_type=action,
                    sending_user=self.scope["user"].username,
                    message=message
                )
                
            
    def game_joined(self, event):
        """
        Called when someone has joined the game.
        """
        if event['game_id'] == int(self.game_id):
            self.send(text_data=render_to_string(
                'game/events/ingame_game_joined.html',
                {
                    'joined_player': event['joined_player'],
                }))

    def game_started(self, event):
        """
        Called when the game has started.
        """
        if event['game_id'] == int(self.game_id):
            data = {
                'game': Game.get_by_id(self.game_id),
                'user': self.scope['user'],
                'starting_chips': event['starting_chips']
            }
            self.send(text_data=
                      render_to_string('game/events/ingame_game_started.html',
                                       data))
            self.send(text_data=
                      render_to_string('game/events/ingame_starting_chips.html',
                                       data))
            
    def game_state_changed(self, event):
        state = event['new_state']
        current_player = event['current_player']
        template = 'game/events/'
        enum_dict = {d.name: str(d.value) for d in GameState}
        
        data = {
            'game': Game.get_by_id(self.game_id),
            'state': str(state),
            'current_player': current_player,
            'user': self.scope['user'],
            'game_states': enum_dict,
            'available_player_targets': event['available_player_targets'],
            'captured_pile_num': event['captured_pile_num'],
            'captured_pile': event['captured_pile'],
            'winner': event['winner'],
            'alive': [str(p) for p in event['alive']],
        }

        if state == GameState.AWAIT_CHOOSE_KILL.value:
            if current_player == self.scope['user'].username:
                response = render_to_string(template + 'ingame_pile_captured.html',data)
                self.send(text_data=response)
            else:
                response = render_to_string(template + 'ingame_pile_captured_others.html',data)
                self.send(text_data=response)

        self.send(text_data=render_to_string(template + 'ingame_state_changed.html',data))


    def game_action(self, event): 
        action_type = event['action_type']
        acting_player = event['acting_player']
        target = event['target']
        used_color = event['used_color']
        
        data = {
            'game': Game.get_by_id(self.game_id),
            'acting_player': acting_player,
            'target': target,
            'used_color': used_color,
            'user': self.scope['user'].username,
            'captured_pile_num': event['captured_pile_num'],
            'captured_pile': event['captured_pile'],
        }

        template = 'game/events/'
        
        if action_type == GameAction.PLAY_MOVE.value:
            if acting_player == self.scope['user'].username:
                return None
            self.send(text_data=render_to_string(template + 'ingame_move_remove.html',data))
            event_template = 'ingame_move_played'
        elif action_type == GameAction.TRANSFER.value:
            if acting_player == self.scope['user'].username:
                return None
            self.send(text_data=render_to_string(template + 'ingame_transfer_remove.html',data))
            event_template = 'ingame_transfer'
        elif action_type == GameAction.KILL_FROM_CAPTURE.value:
            if acting_player != self.scope['user'].username:
                self.send(text_data=render_to_string(template + 'ingame_pile_killed.html', data))
            one_removed = event['captured_pile'][:]
            one_removed.remove(used_color)
            data['captured_pile_one_removed'] = one_removed
            event_template = 'ingame_pile_captured_taken'
            self.send(text_data=render_to_string(template + event_template + '.html',data))
            self.send(text_data=render_to_string(template + 'ingame_pile_killed_to_deadbox.html', data))
            return
        elif action_type == GameAction.PILE_CREATED.value:
            event_template = 'ingame_pile_created'
        elif action_type == GameAction.KILL_PRISONER.value:
            if acting_player == self.scope['user'].username:
                return None
            self.send(text_data=render_to_string(template + 'ingame_transfer_remove.html',data))
            event_template = 'ingame_put_into_deadbox'
        elif action_type == GameAction.PLAYER_KILLED.value:
            event_template = 'ingame_player_killed'
        elif action_type == GameAction.ENTIRE_PILE_KILLED.value:
            self.send(text_data=render_to_string(template + 'ingame_entire_pile_killed.html',data))
            event_template = 'ingame_entire_pile_to_deadbox'
        else:
            return
            
        self.send(text_data=render_to_string(template + event_template + '.html',data))
        
    def game_textmessage(self, event):
        template = 'game/events/'
        data = {
            'sending_user': event['sending_user'],
            'message': event['message'],
        }
        event_template = 'ingame_textmessage'
        self.send(text_data=render_to_string(template + event_template + '.html',data))
