from django.db.models.signals import post_save
import django.dispatch
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()

from .models import Game, Player

from .models import game_started_signal

import game.game_logic as game_logic

def get_game_group(game):
    return 'game_%s' % game.pk

@receiver(post_save, sender=Game)
def new_game_handler(sender, **kwargs):
    game = kwargs['instance']
    if kwargs['created']:
        async_to_sync(channel_layer.group_send)(
            "lobby",
            {
                'type': 'game_created',
                'game_id': game.pk,
            }
        )

@receiver(game_started_signal)
def game_started_handler(sender, **kwargs):
    game = kwargs['game']
    message = {
        'type': 'game_started',
        'game_id': game.pk,
        'starting_chips': kwargs['starting_chips']
    }
    game_group = get_game_group(game)
    async_to_sync(channel_layer.group_send)("lobby", message)
    async_to_sync(channel_layer.group_send)(game_group, message)
            
@receiver(post_save, sender=Player)
def player_joined_handler(sender, **kwargs):
    if kwargs['created']:
        joined_player = kwargs['instance']
        game = joined_player.game
        game_group = get_game_group(game)
        message = {
            'type': 'game_joined',
            'game_id': game.pk,
            'joined_player': joined_player.user.username,
            'player_count': game.get_player_count(),
         }
        async_to_sync(channel_layer.group_send)("lobby", message)
        async_to_sync(channel_layer.group_send)(game_group, message)

@receiver(game_logic.game_state_changed_signal)
def game_state_changed_handler(sender, **kwargs):
    game = kwargs['game']
    game_group = get_game_group(game)

    if kwargs.get('winner'):
        winner = kwargs.get('winner').playername
    else:
        winner = None

    if kwargs.get('alive'):
        alive = [d.playername for d in kwargs.get('alive')]
    else:
        alive = None

    if kwargs['available_player_targets'] is None:
        available_targets = None
    else:
        available_targets = [d.playername for d in kwargs['available_player_targets']]

    new_state = kwargs['new_state'].value
        
    message = {
        'type': 'game_state_changed',
        'game_id': game.pk,
        'new_state': new_state,
        'current_player': kwargs['current_player'].playername,
        'available_player_targets': available_targets,
        'captured_pile': kwargs['captured_pile'],
        'captured_pile_num': kwargs['captured_pile_num'],
        'winner': winner,
        'alive': alive,
    }
    async_to_sync(channel_layer.group_send)(game_group, message)

    if kwargs['new_state'] == game_logic.GameState.FINISHED:
        game.mark_complete(kwargs.get('winner'))
        

@receiver(game_logic.game_action_signal)
def game_action_handler(sender, **kwargs):
    game = kwargs['game']
    game_group = get_game_group(game)
    message = {
        'type': 'game_action',
        'game_id': game.pk,
        'action_type': kwargs['action_type'].value,
        'acting_player': kwargs['acting_player'],
        'target': kwargs['target'],
        'used_color': kwargs['used_color'],
        'captured_pile': kwargs.get('captured_pile'),
        'captured_pile_num': kwargs.get('captured_pile_num'),
    }
    async_to_sync(channel_layer.group_send)(game_group, message)

@receiver(game_logic.concurrent_action_signal)
def concurrent_action_handler(sender, **kwargs):
    game = kwargs['game']
    game_group = get_game_group(game)
    message = {
        'type': 'game_textmessage',
        'game_id': game.pk,
        'action_type': kwargs['action_type'],
        'sending_user': kwargs['sending_user'],
        'message': kwargs['message'],
    }
    async_to_sync(channel_layer.group_send)(game_group, message)
    

