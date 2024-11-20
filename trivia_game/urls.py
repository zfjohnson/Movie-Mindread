from django.urls import path
from . import views

app_name = 'trivia_game'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_movie, name='search_movie'),
    path('movie/<int:movie_id>/', views.get_movie, name='get_movie'),
    path('set_movie/<int:movie_id>/', views.set_movie, name='set_movie'),
    path('guess/', views.make_guess, name='make_guess'),
    path('choose/', views.choose_movie, name='choose_movie'),
    path('guess_movie/', views.guess_movie, name='guess_movie'),
    path('wait/', views.wait_for_guesses, name='wait_for_guesses'),
    path('get_guesses/', views.get_guesses, name='get_guesses'),
]