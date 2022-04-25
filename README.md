# So Long Sucker!
![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/leinfink/so-long-sucker) ![GitHub repo size](https://img.shields.io/github/repo-size/leinfink/so-long-sucker) ![Website](https://img.shields.io/website?url=https%3A%2F%2Fchezhans.uber.space%2Fso-long-sucker%2F)

A parlor game about bargaining and broken promises.

This is an implementation of the four-player game by Hausner et al (1964)[^1], using a django backend and a simple htmx/hyperscript frontend. During a game, it uses websockets to communicate between players (using *django-channels* and *htmx/ws.js*) and stores the live game data in a Redis instance. The finished game is stored seperately in a database.

See it in action here: https://chezhans.uber.space/so-long-sucker/

[^1]: Hausner, M., J. Nash, L. Shapley, and M. Shubik. “‘So Long Sucker’ — a Four-Person Game.” In *Game Theory and Related Approaches to Social Behavior*, edited by Martin Shubik, 359–61. New York: John Wiley & Sons, 1964.
