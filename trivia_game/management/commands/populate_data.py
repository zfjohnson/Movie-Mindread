"""
Management command to populate the database with initial movie data.

This script provides sample data for the Movie Mindread game including:
- Directors
- Studios
- Movies
- Actors
- Genres
- Trivia (Easy, Medium, Hard)

Usage:
    python manage.py populate_data
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from trivia_game.models import Director, Studio, Movie, Actor, Genre, EasyTrivia, MediumTrivia, HardTrivia

class Command(BaseCommand):
    help = 'Populates the database with sample movie data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting database population...')
        
        try:
            with transaction.atomic():
                # Create Directors
                directors = {
                    'christopher_nolan': Director.objects.create(
                        name='Christopher Nolan',
                        debut_movie='Following'
                    ),
                    'steven_spielberg': Director.objects.create(
                        name='Steven Spielberg',
                        debut_movie='Duel'
                    ),
                    'quentin_tarantino': Director.objects.create(
                        name='Quentin Tarantino',
                        debut_movie='Reservoir Dogs'
                    ),
                    'martin_scorsese': Director.objects.create(
                        name='Martin Scorsese',
                        debut_movie='Who\'s That Knocking at My Door'
                    ),
                    'james_cameron': Director.objects.create(
                        name='James Cameron',
                        debut_movie='Piranha II: The Spawning'
                    ),
                    'ridley_scott': Director.objects.create(
                        name='Ridley Scott',
                        debut_movie='The Duellists'
                    ),
                    'peter_jackson': Director.objects.create(
                        name='Peter Jackson',
                        debut_movie='Bad Taste'
                    ),
                }
                self.stdout.write('Created directors')

                # Create Studios
                studios = {
                    'warner': Studio.objects.create(
                        name='Warner Bros.',
                        address='4000 Warner Blvd, Burbank, CA'
                    ),
                    'universal': Studio.objects.create(
                        name='Universal Pictures',
                        address='100 Universal City Plaza, Universal City, CA'
                    ),
                    'miramax': Studio.objects.create(
                        name='Miramax',
                        address='1901 Avenue of the Stars, Los Angeles, CA'
                    ),
                    'paramount': Studio.objects.create(
                        name='Paramount Pictures',
                        address='5555 Melrose Avenue, Hollywood, CA'
                    ),
                    'twentieth': Studio.objects.create(
                        name='20th Century Studios',
                        address='10201 West Pico Blvd., Los Angeles, CA'
                    ),
                    'newline': Studio.objects.create(
                        name='New Line Cinema',
                        address='4000 Warner Boulevard, Burbank, CA'
                    ),
                }
                self.stdout.write('Created studios')

                # Create Movies
                movies = {
                    'inception': Movie.objects.create(
                        title='Inception',
                        month='July',
                        day=16,
                        year=2010,
                        director=directors['christopher_nolan']
                    ),
                    'jurassic_park': Movie.objects.create(
                        title='Jurassic Park',
                        month='June',
                        day=11,
                        year=1993,
                        director=directors['steven_spielberg']
                    ),
                    'pulp_fiction': Movie.objects.create(
                        title='Pulp Fiction',
                        month='October',
                        day=14,
                        year=1994,
                        director=directors['quentin_tarantino']
                    ),
                    'goodfellas': Movie.objects.create(
                        title='Goodfellas',
                        month='September',
                        day=19,
                        year=1990,
                        director=directors['martin_scorsese']
                    ),
                    'titanic': Movie.objects.create(
                        title='Titanic',
                        month='December',
                        day=19,
                        year=1997,
                        director=directors['james_cameron']
                    ),
                    'alien': Movie.objects.create(
                        title='Alien',
                        month='May',
                        day=25,
                        year=1979,
                        director=directors['ridley_scott']
                    ),
                    'lotr_fellowship': Movie.objects.create(
                        title='The Lord of the Rings: The Fellowship of the Ring',
                        month='December',
                        day=19,
                        year=2001,
                        director=directors['peter_jackson']
                    ),
                    'dark_knight': Movie.objects.create(
                        title='The Dark Knight',
                        month='July',
                        day=18,
                        year=2008,
                        director=directors['christopher_nolan']
                    ),
                    'gladiator': Movie.objects.create(
                        title='Gladiator',
                        month='May',
                        day=5,
                        year=2000,
                        director=directors['ridley_scott']
                    ),
                    'avatar': Movie.objects.create(
                        title='Avatar',
                        month='December',
                        day=18,
                        year=2009,
                        director=directors['james_cameron']
                    ),
                }
                self.stdout.write('Created movies')

                # Link Movies and Studios
                movies['inception'].studios.add(studios['warner'])
                movies['jurassic_park'].studios.add(studios['universal'])
                movies['pulp_fiction'].studios.add(studios['miramax'])
                movies['goodfellas'].studios.add(studios['warner'])
                movies['titanic'].studios.add(studios['paramount'])
                movies['alien'].studios.add(studios['twentieth'])
                movies['lotr_fellowship'].studios.add(studios['newline'])
                movies['dark_knight'].studios.add(studios['warner'])
                movies['gladiator'].studios.add(studios['universal'])
                movies['avatar'].studios.add(studios['twentieth'])

                # Create Actors
                actors = {
                    'leonardo': Actor.objects.create(name='Leonardo DiCaprio'),
                    'sam': Actor.objects.create(name='Sam Neill'),
                    'john': Actor.objects.create(name='John Travolta'),
                    'robert': Actor.objects.create(name='Robert De Niro'),
                    'kate': Actor.objects.create(name='Kate Winslet'),
                    'sigourney': Actor.objects.create(name='Sigourney Weaver'),
                    'elijah': Actor.objects.create(name='Elijah Wood'),
                    'christian': Actor.objects.create(name='Christian Bale'),
                    'russell': Actor.objects.create(name='Russell Crowe'),
                    'zoe': Actor.objects.create(name='Zoe Saldana'),
                }
                self.stdout.write('Created actors')

                # Link Actors to Movies
                actors['leonardo'].movies.add(movies['inception'], movies['titanic'])
                actors['sam'].movies.add(movies['jurassic_park'])
                actors['john'].movies.add(movies['pulp_fiction'])
                actors['robert'].movies.add(movies['goodfellas'])
                actors['kate'].movies.add(movies['titanic'])
                actors['sigourney'].movies.add(movies['alien'], movies['avatar'])
                actors['elijah'].movies.add(movies['lotr_fellowship'])
                actors['christian'].movies.add(movies['dark_knight'])
                actors['russell'].movies.add(movies['gladiator'])
                actors['zoe'].movies.add(movies['avatar'])

                # Add Genres
                for movie, genres_list in {
                    'inception': ['Sci-Fi', 'Action', 'Thriller'],
                    'jurassic_park': ['Adventure', 'Sci-Fi', 'Thriller'],
                    'pulp_fiction': ['Crime', 'Drama', 'Thriller'],
                    'goodfellas': ['Crime', 'Drama', 'Biography'],
                    'titanic': ['Drama', 'Romance', 'History'],
                    'alien': ['Horror', 'Sci-Fi', 'Thriller'],
                    'lotr_fellowship': ['Fantasy', 'Adventure', 'Drama'],
                    'dark_knight': ['Action', 'Crime', 'Drama'],
                    'gladiator': ['Action', 'Drama', 'History'],
                    'avatar': ['Sci-Fi', 'Action', 'Adventure'],
                }.items():
                    for genre in genres_list:
                        Genre.objects.create(movie=movies[movie], type=genre)
                self.stdout.write('Created genres')

                # Add Trivia
                trivia_data = {
                    'inception': {
                        'easy': [
                            "This movie was released in 2010",
                            "Leonardo DiCaprio plays the main character",
                            "The movie is about dreams"
                        ],
                        'medium': [
                            "The movie's tagline was 'Your mind is the scene of the crime'",
                            "Hans Zimmer composed the iconic soundtrack",
                            "The spinning top is a recurring symbol"
                        ],
                        'hard': [
                            "The snow fortress sequence was filmed in Calgary, Alberta",
                            "The character Mal is named after the French word for 'bad'",
                            "The runtime is exactly 2 hours and 28 minutes"
                        ]
                    },
                    'jurassic_park': {
                        'easy': [
                            "This movie features dinosaurs",
                            "It was released in 1993",
                            "The movie takes place on an island"
                        ],
                        'medium': [
                            "The T-Rex animatronic sometimes malfunctioned due to rain",
                            "The raptor sounds were a mix of various animal noises",
                            "The movie was based on a Michael Crichton novel"
                        ],
                        'hard': [
                            "The velociraptor sounds were created using tortoises mating",
                            "Hurricane Iniki hit during filming in Hawaii",
                            "The T-Rex roar was made from a baby elephant's sound"
                        ]
                    },
                    'dark_knight': {
                        'easy': [
                            "This movie features Batman",
                            "It was released in 2008",
                            "Heath Ledger plays the Joker"
                        ],
                        'medium': [
                            "The movie was partially filmed in Chicago",
                            "Heath Ledger won a posthumous Oscar",
                            "The Batpod was a fully functional vehicle"
                        ],
                        'hard': [
                            "The hospital explosion was real and done in one take",
                            "The Joker's scars change stories throughout the film",
                            "The IMAX cameras used were so loud that dialogue had to be re-recorded"
                        ]
                    },
                }

                for movie_key, trivia in trivia_data.items():
                    movie = movies[movie_key]
                    for easy_fact in trivia['easy']:
                        EasyTrivia.objects.create(movie=movie, trivia_fact=easy_fact)
                    for medium_fact in trivia['medium']:
                        MediumTrivia.objects.create(movie=movie, trivia_fact=medium_fact)
                    for hard_fact in trivia['hard']:
                        HardTrivia.objects.create(movie=movie, trivia_fact=hard_fact)

                self.stdout.write('Created trivia')
                self.stdout.write(self.style.SUCCESS('Successfully populated database'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error populating database: {str(e)}')
            )
