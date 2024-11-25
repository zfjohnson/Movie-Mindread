from django.contrib import admin
from .models import Movie, Actor, Studio, Director, Trivia

# Register your models here.

@admin.register(Studio)
class StudioAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    search_fields = ('name',)

@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'debut_movie')
    search_fields = ('name', 'debut_movie')

@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_date', 'genre', 'director', 'studio', 'imdb_rating')
    list_filter = ('genre', 'release_date', 'studio', 'director')
    search_fields = ('title', 'director__name', 'studio__name')
    filter_horizontal = ('actors',)
    
@admin.register(Trivia)
class TriviaAdmin(admin.ModelAdmin):
    list_display = ('movie', 'difficulty', 'trivia_fact', 'created_at')
    list_filter = ('difficulty', 'movie', 'created_at')
    search_fields = ('movie__title', 'trivia_fact')
    readonly_fields = ('created_at', 'updated_at')