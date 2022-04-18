from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.lobby, name='lobby'),
    path('game/<int:pk>/', views.game, name='game'),
    path('game/create/', views.create_game, name='create_game'),
    path('game/join/<int:pk>/', views.join_game, name='join_game'),
    path('game/<int:pk>/getboard', views.get_game_board, name='get_gameboard'),
    path('game/<int:pk>/getstate', views.get_game_state, name='get_gamestate')
    ]
