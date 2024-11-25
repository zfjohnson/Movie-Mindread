from django.core.management.base import BaseCommand
from django.db import transaction
from trivia_game.models import Movie, Actor, Director, Studio
import imdb
import time
import sys

class Command(BaseCommand):
    help = 'Fetches movie data from IMDb and populates the database'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=25, help='Number of top movies to fetch')

    def handle(self, *args, **options):
        ia = imdb.Cinemagoer()
        count = options['count']
        
        self.stdout.write(self.style.SUCCESS(f'Fetching {count} movies from IMDb...'))
        

        top250 = ia.get_top250_movies()
        self.stdout.write(f'Found {len(top250)} movies in Top 250')
        movie_ids = []
        for movie in top250:
            movie_id = movie.getID()
            movie_ids.append(movie_id)
            self.stdout.write(f'Added movie ID: {movie_id} - {movie.get("title", "Unknown Title")}')
            if len(movie_ids) >= count:
                break

        self.stdout.write(f'Processing {len(movie_ids)} movies: {movie_ids}')
        # Process movies
        successful_imports = 0
        for movie_id in movie_ids:
            try:
                with transaction.atomic():
                    self.stdout.write(f'Processing movie {successful_imports+1}/{count}: ID={movie_id}')
                    
                    # Fetch movie details
                    try:
                        movie_data = ia.get_movie(movie_id)
                        self.stdout.write(f'Successfully fetched movie data for ID {movie_id}')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Failed to fetch movie {movie_id}: {str(e)}'))
                        continue

                    # Create or get studio
                    studio_name = "Unknown Studio"
                    companies = movie_data.get('production companies', [])
                    if companies:
                        studio_name = str(companies[0])[:200]
                    
                    studio, created = Studio.objects.get_or_create(
                        name=studio_name,
                        defaults={'address': 'Address not available'}
                    )
                    self.stdout.write(f'{"Created" if created else "Using existing"} studio: {studio.name}')
                    
                    # Create or get director
                    director_name = "Unknown Director"
                    directors = movie_data.get('directors', [])
                    if directors:
                        director_name = str(directors[0])[:200]
                    
                    director, created = Director.objects.get_or_create(
                        name=director_name,
                        defaults={'debut_movie': 'Unknown'}
                    )
                    self.stdout.write(f'{"Created" if created else "Using existing"} director: {director.name}')
                    
                    # Create movie
                    title = str(movie_data.get('title', 'Unknown Title'))[:200]
                    year = movie_data.get('year', 2000)
                    if not isinstance(year, int):
                        year = 2000
                    
                    genres = movie_data.get('genres', ['Unknown'])[:3]
                    genre_str = ', '.join(str(g) for g in genres)[:100]
                    
                    rating = movie_data.get('rating', 0.0)
                    if not isinstance(rating, (int, float)):
                        rating = 0.0
                    
                    self.stdout.write(f'Creating movie: {title} ({year})')
                    
                    movie = Movie.objects.create(
                        title=title,
                        release_date=year,
                        genre=genre_str,
                        studio=studio,
                        director=director,
                        imdb_rating=float(rating)
                    )
                    self.stdout.write(f'Created movie: {movie.title}')
                    
                    # Add actors
                    cast = movie_data.get('cast', [])[:6]  # Limit to top 6 actors
                    for actor_data in cast:
                        actor_name = str(actor_data)[:200]
                        actor, created = Actor.objects.get_or_create(
                            name=actor_name
                        )
                        movie.actors.add(actor)
                        self.stdout.write(f'{"Created" if created else "Using existing"} actor: {actor.name}')
                    
                    successful_imports += 1
                    self.stdout.write(self.style.SUCCESS(f'Successfully processed: {movie.title}'))
                    time.sleep(1)  # Rate limiting
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing movie {movie_id}: {str(e)}'))
                self.stdout.write(self.style.ERROR(f'Full error: {sys.exc_info()}'))
                continue
        
        self.stdout.write(self.style.SUCCESS(f'Data import completed. Successfully imported {successful_imports}/{count} movies.'))
