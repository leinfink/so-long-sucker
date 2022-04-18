from django.contrib import admin

from .models import Game

class GameAdmin(admin.ModelAdmin):
    list_display = ('pk',
                    'creator',
                    'winner',
                    'created',
                    'started',
                    'completed',
                    'modified',
                    )

admin.site.register(Game, GameAdmin)
