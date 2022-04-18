from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.core.paginator import Paginator

from .models import Player, Game
from config.utils import get_base_template
from game.utils import get_game_through_redis
from game.game_logic import GameState, GameRun

@never_cache
def lobby(request: HttpRequest) -> HttpResponse:
    user = request.user

    open_games =  list(Game.get_open_games_not_joined_by_user(user))
    og_page_num = request.GET.get("og_page", "1")
    og_paginator = Paginator(object_list=open_games, per_page=15)
    og_page = og_paginator.get_page(og_page_num)

    player_games =  list(Game.get_games_for_player(user))
    pg_page_num = request.GET.get("pg_page", "1")
    pg_paginator = Paginator(object_list=player_games, per_page=15)
    pg_page = pg_paginator.get_page(pg_page_num)
    
    return render(
        request,
        "game/lobby.html",
        {
            "base_template": get_base_template(request),
            "open_games": og_page,
            "player_games": pg_page,
            "total_games": Game.get_total_number_of_games(),
        },
    )

    
@never_cache
def game(request: HttpRequest, pk) -> HttpResponse:
    return render(
        request,
        "game/game.html",
        { 
            "base_template": get_base_template(request),
            "game": Game.get_by_id(pk),
        },
   )

@never_cache
def get_game_board(request: HttpRequest, pk) -> HttpResponse:
    if not request.htmx:
        return game(request, pk)
    else:
        game = Game.get_by_id(pk)
        if game.started == None:
            return render(
            request,
                "game/game_board.html",
                { 
                    "base_template": get_base_template(request),
                    "game": game,
                },
        ) 
        else:
            gameRun = get_game_through_redis(pk)
            enum_dict = {d.name: str(d.value) for d in GameState}
            return render(
                request,
                "game/game_board_running.html",
                { 
                    "base_template": get_base_template(request),
                    "gameRun": gameRun,
                    "game_states": enum_dict,
                },
            ) 

@never_cache
def get_game_state(request: HttpRequest, pk) -> HttpResponse:
    if not request.htmx:
        return HttpResponse(status=204)
    else:
        game = Game.get_by_id(pk)
        if game.started == None:
            return HttpResponse(status=204)
        else:
            available_player_targets = None
            captured_pile = None
            captured_pile_num = None
            winner = None
        
            gameRun = get_game_through_redis(pk)
            enum_dict = {d.name: str(d.value) for d in GameState}
            state = gameRun.state
            if state == GameState.AWAIT_GIVE_MOVE:
                available_colors = GameRun.possible_moves(
                    gameRun.get_living_colors(),
                    gameRun.playing_area[gameRun.last_played_pile]
                )
                available_player_targets = [gameRun.players[p] for p in available_colors]
            elif state == GameState.AWAIT_CHOOSE_KILL:
                captured_pile = gameRun.playing_area[gameRun.last_played_pile]
                captured_pile_num = gameRun.last_played_pile
            elif state == GameState.FINISHED:
                winner = gameRun.winner
                
            return render(
                request,
                "game/game_state_running.html",
                { 
                    "base_template": get_base_template(request),
                    "game": gameRun.db_game,
                    "game_states": enum_dict,
                    "current_player": gameRun.current_player,
                    "state": str(gameRun.state.value),
                    "available_player_targets": available_player_targets,
                    "captured_pile_num": captured_pile_num,
                    "captured_pile": captured_pile,
                    "winner": winner,
                    "alive": [str(p) for p in gameRun.get_living_players()]
                },
            ) 
        

@never_cache
@require_POST
def create_game(request: HttpRequest) -> HttpResponse:
    new_game = Game.create_new(request.user)
    response =  render(
        request,
        "game/game.html",
        {
            "base_template": get_base_template(request),
            "game": new_game,
        },
   )

    response['HX-Push'] = reverse('game', kwargs={'pk': new_game.pk})
    return response

@never_cache
@require_POST
def join_game(request: HttpRequest, pk) -> HttpResponse:
    game = Game.get_by_id(pk)
    game.player_join(request.user)
    
    return render(
        request,
        "game/game.html",
        {
            "base_template": get_base_template(request),
            "game": game,
        },
   ) 
