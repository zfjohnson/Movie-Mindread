from django.contrib import admin
from .models import (
    Movie, Actor, Studio, Director,
    ProductionCompany, EasyTrivia, MediumTrivia, HardTrivia
)

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
    list_display = ('title', 'release_date', 'genre', 'imdb_rating')
    list_filter = ('genre', 'release_date')
    search_fields = ('title', 'genre')

@admin.register(ProductionCompany)
class ProductionCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'movie', 'founding_year', 'headquarters')
    list_filter = ('founding_year',)
    search_fields = ('name', 'movie__title', 'headquarters')

@admin.register(EasyTrivia)
class EasyTriviaAdmin(admin.ModelAdmin):
    list_display = ('movie', 'trivia_fact', 'created_at')
    list_filter = ('movie', 'created_at')
    search_fields = ('movie__title', 'trivia_fact')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(MediumTrivia)
class MediumTriviaAdmin(admin.ModelAdmin):
    list_display = ('movie', 'trivia_fact', 'created_at')
    list_filter = ('movie', 'created_at')
    search_fields = ('movie__title', 'trivia_fact')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(HardTrivia)
class HardTriviaAdmin(admin.ModelAdmin):
    list_display = ('movie', 'trivia_fact', 'created_at')
    list_filter = ('movie', 'created_at')
    search_fields = ('movie__title', 'trivia_fact')
    readonly_fields = ('created_at', 'updated_at')
