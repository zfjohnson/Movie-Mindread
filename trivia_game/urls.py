<<<<<<< HEAD
from django.urls import path
=======
from django.contrib import admin
from django.urls import include, path

>>>>>>> sqlite-version
from . import views

app_name = 'trivia_game'

urlpatterns = [
<<<<<<< HEAD
    path('', views.index, name='index'),
    path('search/', views.search_movie, name='search_movie'),
    path('movie/<int:movie_id>/', views.get_movie, name='get_movie'),
    path('set_movie/<int:movie_id>/', views.set_movie, name='set_movie'),
    path('guess/', views.make_guess, name='make_guess'),
    path('choose/', views.choose_movie, name='choose_movie'),
    path('guess_movie/', views.guess_movie, name='guess_movie'),
    path('wait/', views.wait_for_guesses, name='wait_for_guesses'),
    path('get_guesses/', views.get_guesses, name='get_guesses'),
=======
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
>>>>>>> sqlite-version
]