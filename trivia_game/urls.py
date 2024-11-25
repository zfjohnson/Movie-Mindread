from django.contrib import admin
from django.urls import include, path

from . import views

app_name = 'trivia_game'

urlpatterns = [
    path("", views.index, name="index"),
    path('choose/', views.choose_movie, name='choose_movie'),
    path('start/<int:movie_id>/', views.start_game, name='start_game'),
    path('play/', views.play_game, name='play_game'),
    path('guess/', views.make_guess, name='make_guess'),
    path('game-over/', views.game_over, name='game_over'),
    path('info/<int:movie_id>/', views.movie_info, name='movie_info'),
    path('manage/', views.manage_movies, name='manage_movies'),
    path('add/', views.add_movie, name='add_movie'),
    path('delete/<int:movie_id>/', views.delete_movie, name='delete_movie'),
]