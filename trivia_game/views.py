from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .models import (
    Movie, Director, Studio, ProductionCompany,
    EasyTrivia, MediumTrivia, HardTrivia, Actor
)
import random
import json
from django.db.models import Avg, Count

class TriviaQuality:
    """Tracks the quality and source of generated trivia facts.
    
    Quality Levels:
    - HIGH (3): Database-sourced trivia facts
    - MEDIUM (2): Direct movie attributes (director, year, etc.)
    - LOW (1): Fallback or generic trivia
    """
    HIGH = 3    # Database trivia
    MEDIUM = 2  # Direct movie attributes
    LOW = 1     # Fallback/generic trivia

class TriviaResult:
    """Encapsulates a trivia fact with its metadata.
    
    Attributes:
        fact (str): The actual trivia text
        quality (TriviaQuality): Quality level of the trivia
        source (str): Source of the trivia (database, actor, director, etc.)
    """
    def __init__(self, fact, quality, source):
        self.fact = fact
        self.quality = quality
        self.source = source

def index(request):
    # Clear any existing game state
    if 'game_state' in request.session:
        del request.session['game_state']
    return render(request, "index.html")

def manage_movies(request):
    movies = Movie.objects.all().order_by('title')
    return render(request, "trivia_game/manage_movies.html", {
        'movies': movies
    })

def add_movie(request):
    if request.method == 'POST':
        try:
            # Create or get Director if provided
            director = None
            if request.POST.get('director'):
                director, _ = Director.objects.get_or_create(
                    name=request.POST['director']
                )

            # Create or get Studio if provided
            studio = None
            if request.POST.get('studio'):
                studio, _ = Studio.objects.get_or_create(
                    name=request.POST['studio']
                )

            # Create the movie
            movie = Movie.objects.create(
                title=request.POST['title'],
                release_date=int(request.POST['release_date']),
                genre=request.POST['genre'],
                imdb_rating=float(request.POST['imdb_rating']),
                director=director,
                studio=studio
            )

            # Create Production Company if provided
            if request.POST.get('production_company'):
                ProductionCompany.objects.create(
                    name=request.POST['production_company'],
                    founding_year=int(request.POST['production_company_year']) if request.POST.get('production_company_year') else None,
                    headquarters=request.POST.get('production_company_hq', ''),
                    movie=movie
                )

            # Create trivia entries if provided
            if request.POST.get('easy_trivia'):
                EasyTrivia.objects.create(
                    movie=movie,
                    trivia_fact=request.POST['easy_trivia']
                )

            if request.POST.get('medium_trivia'):
                MediumTrivia.objects.create(
                    movie=movie,
                    trivia_fact=request.POST['medium_trivia']
                )

            if request.POST.get('hard_trivia'):
                HardTrivia.objects.create(
                    movie=movie,
                    trivia_fact=request.POST['hard_trivia']
                )
            
            return JsonResponse({
                'success': True,
                'movie': {
                    'id': movie.id,
                    'title': movie.title,
                    'release_date': movie.release_date,
                    'genre': movie.genre,
                    'imdb_rating': str(movie.imdb_rating),
                    'director': movie.director.name if movie.director else 'Unknown',
                    'studio': movie.studio.name if movie.studio else 'Unknown'
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_protect
def delete_movie(request, movie_id):
    if request.method == 'POST':
        try:
            movie = get_object_or_404(Movie, pk=movie_id)
            # Check if the movie has any active games
            if 'game_state' in request.session:
                game_state = request.session['game_state']
                if game_state.get('movie_id') == movie_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Cannot delete movie: it is currently being used in an active game'
                    })
            movie.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

def choose_movie(request):
    """First phase: Select a movie to guess"""
    if request.method == 'POST':
        movie_id = request.POST.get('movie_id')
        if not movie_id:
            return redirect('choose_movie')
            
        # Initialize game state
        game_state = {
            'movie_id': movie_id,
            'attempts_left': 9,
            'revealed_trivia': [],
            'used_trivia': [],  # Initialize empty list for used trivia
            'won': False,
            'game_over': False
        }
        request.session['game_state'] = game_state
        
        return redirect('play_game')
    else:
        sort_by = request.GET.get('sort')
        if sort_by == 'highest':
            movies = Movie.objects.all().order_by('-imdb_rating', 'title')
        elif sort_by == 'lowest':
            movies = Movie.objects.all().order_by('imdb_rating', 'title')
        else:
            movies = Movie.objects.all().order_by('title')
            
        return render(request, "trivia_game/choose_movie.html", {
            'movies': movies,
            'phase': 'chooser'
        })

def movie_info(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    return render(request, "trivia_game/movie_info.html", {
        'movie': movie
    })

def edit_movie(request, movie_id):
    """Edit an existing movie"""
    movie = get_object_or_404(Movie, pk=movie_id)
    
    if request.method == 'POST':
        # Update movie details
        movie.title = request.POST.get('title')
        movie.release_date = request.POST.get('release_date')
        movie.genre = request.POST.get('genre')
        movie.imdb_rating = request.POST.get('imdb_rating')
        
        # Get or create director
        director_name = request.POST.get('director')
        if director_name:
            director, _ = Director.objects.get_or_create(name=director_name)
            movie.director = director
        
        # Get or create studio
        studio_name = request.POST.get('studio')
        if studio_name:
            studio, _ = Studio.objects.get_or_create(name=studio_name)
            movie.studio = studio
        
        movie.save()

        # Update actors
        actor_names = request.POST.get('actors', '').strip().split('\n')
        # Clear existing actors
        movie.actors.clear()
        # Add new actors
        for name in actor_names:
            name = name.strip()
            if name:
                actor, _ = Actor.objects.get_or_create(name=name)
                movie.actors.add(actor)
        
        # Update or create production company
        production_company_name = request.POST.get('production_company')
        if production_company_name:
            ProductionCompany.objects.update_or_create(
                movie=movie,
                defaults={
                    'name': production_company_name,
                    'founding_year': request.POST.get('production_company_year') or None,
                    'headquarters': request.POST.get('production_company_hq', '')
                }
            )
        
        # Update trivia facts - Easy
        easy_trivia = request.POST.get('easy_trivia')
        if easy_trivia:
            EasyTrivia.objects.update_or_create(
                movie=movie,
                defaults={'trivia_fact': easy_trivia}
            )
        else:
            EasyTrivia.objects.filter(movie=movie).delete()
        
        # Update trivia facts - Medium
        medium_trivia = request.POST.get('medium_trivia')
        if medium_trivia:
            MediumTrivia.objects.update_or_create(
                movie=movie,
                defaults={'trivia_fact': medium_trivia}
            )
        else:
            MediumTrivia.objects.filter(movie=movie).delete()
        
        # Update trivia facts - Hard
        hard_trivia = request.POST.get('hard_trivia')
        if hard_trivia:
            HardTrivia.objects.update_or_create(
                movie=movie,
                defaults={'trivia_fact': hard_trivia}
            )
        else:
            HardTrivia.objects.filter(movie=movie).delete()
        
        return redirect('manage_movies')
    
    context = {
        'movie': movie,
        'production_company': ProductionCompany.objects.filter(movie=movie).first(),
        'easy_trivia': EasyTrivia.objects.filter(movie=movie).first(),
        'medium_trivia': MediumTrivia.objects.filter(movie=movie).first(),
        'hard_trivia': HardTrivia.objects.filter(movie=movie).first(),
    }
    
    return render(request, "trivia_game/edit_movie.html", context)

def start_game(request, movie_id=None):
    """Start a new game with the selected movie or a random one"""
    try:
        if movie_id:
            movie = get_object_or_404(Movie, pk=movie_id)
        else:
            # Get all movies
            all_movies = Movie.objects.all()
            if not all_movies.exists():
                messages.error(request, "No movies available to play with!")
                return redirect('manage_movies')
            # Select a random movie
            movie = random.choice(all_movies)
        
        # Clear any existing game state
        if 'game_state' in request.session:
            del request.session['game_state']
        
        # Get first hard trivia
        first_trivia = get_first_trivia(movie)
        
        # Initialize game state with first trivia already shown
        game_state = {
            'movie_id': movie.id,
            'attempts_left': 9,  # Start with 9 attempts
            'used_trivia': [first_trivia.fact],
            'revealed_trivia': [{
                'trivia_fact': first_trivia.fact,
                'difficulty': 'H'
            }],
            'won': False,
            'game_over': False,
            'first_trivia_shown': True  # Flag to track first trivia
        }
        request.session['game_state'] = game_state
        
        # Redirect to play_game with movie_id
        return redirect('play_game', movie_id=movie.id)

    except Exception as e:
        print(f"Error in start_game: {str(e)}")
        messages.error(request, "Error starting game. Please try again.")
        return redirect('choose_movie')

def get_first_trivia(movie):
    """Get the first hard trivia for a movie"""
    # Try to get hard trivia from database first
    hard_trivia = HardTrivia.objects.filter(movie=movie).first()
    if hard_trivia:
        return TriviaResult(hard_trivia.trivia_fact, TriviaQuality.HIGH, "database")
    
    # Fallback hard trivia options if no database entry
    hard_fallbacks = [
        "This film pushed the boundaries of what was possible in cinema.",
        "The movie was groundbreaking for its time.",
        "This film set new standards in filmmaking.",
        "Known for its innovative approach to storytelling.",
        "The film represents a milestone in cinema history."
    ]
    return TriviaResult(random.choice(hard_fallbacks), TriviaQuality.HIGH, "fallback")

def play_game(request, movie_id=None):
    """Start or continue a game session"""
    try:
        # Initialize new game if no existing game state
        if 'game_state' not in request.session:
            if not movie_id:
                return redirect('choose_movie')
            
            movie = get_object_or_404(Movie, pk=movie_id)
            
            # Get first hard trivia
            first_trivia = get_first_trivia(movie)
            
            # Initialize game state with first trivia already shown
            game_state = {
                'movie_id': movie_id,
                'attempts_left': 9,  # Start with 9 attempts
                'used_trivia': [first_trivia.fact],
                'revealed_trivia': [{
                    'trivia_fact': first_trivia.fact,
                    'difficulty': 'H'
                }],
                'won': False,
                'game_over': False,
                'first_trivia_shown': True  # Flag to track first trivia
            }
            
            request.session['game_state'] = game_state
        else:
            game_state = request.session['game_state']
            if not game_state or game_state.get('game_over', False):
                return redirect('choose_movie')

        return render(request, "trivia_game/play_game.html", {
            'attempts_left': game_state['attempts_left'],
            'revealed_trivia': game_state['revealed_trivia'],
            'game_over': game_state.get('game_over', False),
            'progress_percentage': int((game_state['attempts_left'] / 9) * 100)
        })
        
    except Exception as e:
        print(f"Error in play_game: {str(e)}")
        return redirect('choose_movie')

def generate_trivia(movie, num_guesses, used_trivia=None):
    """Generate trivia based on number of guesses and movie data"""
    if used_trivia is None:
        used_trivia = []

    # Define the strict order of trivia types
    trivia_order = [
        ('release_year', None, TriviaQuality.HIGH),           # 0: Release Year (Hard)
        ('studio', None, TriviaQuality.HIGH),                 # 1: Studio (Hard)
        ('medium_trivia', MediumTrivia, TriviaQuality.MEDIUM), # 2: Medium Trivia
        ('production', None, TriviaQuality.MEDIUM),           # 3: Production Company
        ('genre', None, TriviaQuality.MEDIUM),                # 4: Genre
        ('easy_trivia', EasyTrivia, TriviaQuality.LOW),      # 5: Easy Trivia
        ('actors', None, TriviaQuality.LOW),                  # 6: Actors
        ('director', None, TriviaQuality.LOW),                # 7: Director (Last)
    ]

    if num_guesses >= len(trivia_order):
        return TriviaResult(
            f"This is your last chance to guess the movie!",
            TriviaQuality.LOW,
            "final_hint"
        )

    trivia_type, model, quality = trivia_order[num_guesses]

    # Try database trivia first for the appropriate models
    if model and model.objects.filter(movie=movie).exists():
        available_trivia = model.objects.filter(
            movie=movie
        ).exclude(trivia_fact__in=used_trivia)
        
        if available_trivia.exists():
            trivia = random.choice(list(available_trivia))
            return TriviaResult(trivia.trivia_fact, quality, "database")

    # Generate dynamic trivia based on the strict order
    if trivia_type == 'release_year':
        if movie.release_date:
            facts = [
                f"Released in {movie.release_date}.",
                f"Made its debut in {movie.release_date}.",
                f"Hit theaters in {movie.release_date}."
            ]
        else:
            facts = [
                "This film's release marked a significant moment in cinema.",
                "The timing of this film's release was carefully chosen.",
                "The release of this film was highly anticipated."
            ]

    elif trivia_type == 'studio':
        if movie.studio:
            facts = [
                f"Brought to you by {movie.studio.name}.",
                f"A {movie.studio.name} production.",
                f"Created at {movie.studio.name} studios."
            ]
        else:
            facts = [
                "This film was produced by a notable studio.",
                "The studio behind this film is known for quality productions.",
                "Made by a studio with a distinctive style."
            ]

    elif trivia_type == 'production':
        production_companies = movie.production_companies.all()
        if production_companies.exists():
            company = production_companies.first()
            facts = [
                f"Produced by {company.name}.",
                f"A {company.name} production.",
                f"Made under the {company.name} banner."
            ]
        else:
            facts = [
                "The production of this film was a significant undertaking.",
                "Created through a unique production process.",
                "This production brought together various talented teams."
            ]

    elif trivia_type == 'genre':
        if movie.genre:
            facts = [
                f"This is a {movie.genre} movie.",
                f"Falls into the {movie.genre} category.",
                f"A prime example of the {movie.genre} genre."
            ]
        else:
            facts = [
                "This film defies traditional genre classifications.",
                "Known for its unique blend of styles.",
                "Creates its own category in filmmaking."
            ]

    elif trivia_type == 'actors':
        actors = movie.actors.all()
        if actors.exists():
            actor_names = [actor.name for actor in actors[:2]]
            facts = [
                f"Stars {', '.join(actor_names)}.",
                f"Features performances by {', '.join(actor_names)}.",
                f"Showcases the talents of {', '.join(actor_names)}."
            ]
        else:
            facts = [
                "Features memorable performances from its cast.",
                "The cast brings unique energy to their roles.",
                "Known for its powerful acting performances."
            ]

    elif trivia_type == 'director':
        if movie.director:
            facts = [
                f"Directed by {movie.director.name}.",
                f"A film from director {movie.director.name}.",
                f"Helmed by {movie.director.name}."
            ]
        else:
            facts = [
                "Directed with a distinctive visual style.",
                "The director's vision shines through in every scene.",
                "Shows masterful direction throughout."
            ]

    else:  # Fallback for medium/easy trivia when no database entries exist
        quality_facts = {
            TriviaQuality.MEDIUM: [
                "The production involved several unique creative choices.",
                "Notable for its distinctive artistic approach.",
                "Created with attention to every detail."
            ],
            TriviaQuality.LOW: [
                "This film tells a compelling story.",
                "Known for its memorable moments.",
                "A noteworthy addition to cinema."
            ]
        }
        facts = quality_facts[quality]

    # Filter out used facts
    unused_facts = [f for f in facts if f not in used_trivia]
    if unused_facts:
        return TriviaResult(random.choice(unused_facts), quality, f"{trivia_type}_dynamic")

    # Ultimate fallback specific to the trivia type
    fallback_facts = {
        'release_year': "The release timing was significant.",
        'studio': "Created by a notable production house.",
        'medium_trivia': "The production process was unique.",
        'production': "Produced with great attention to detail.",
        'genre': "Represents its genre in a unique way.",
        'easy_trivia': "Has left its mark on cinema.",
        'actors': "Features memorable performances.",
        'director': "Shows strong directorial vision."
    }

    return TriviaResult(
        fallback_facts[trivia_type],
        quality,
        f"{trivia_type}_fallback"
    )

@require_POST
def make_guess(request):
    """Handle a movie guess"""
    try:
        game_state = request.session.get('game_state')
        if not game_state:
            return JsonResponse({'error': 'No active game'}, status=400)

        guess = request.POST.get('guess', '').strip()
        if not guess:
            return JsonResponse({'error': 'No guess provided'}, status=400)

        movie = get_object_or_404(Movie, pk=game_state['movie_id'])
        is_correct = guess.lower() == movie.title.lower()
        
        if is_correct:
            game_state['won'] = True
            game_state['score'] = calculate_score(movie, 9 - game_state['attempts_left'])
            request.session.modified = True
            return JsonResponse({
                'correct': True,
                'message': f'Congratulations! You correctly guessed the movie: {movie.title}',
                'movie_title': movie.title,
                'score': game_state['score']
            })
        
        # Handle incorrect guess
        game_state['attempts_left'] -= 1
        
        # Check if game is over due to no more attempts
        if game_state['attempts_left'] <= 0:
            game_state['won'] = False
            game_state['score'] = 0
            request.session.modified = True
            return JsonResponse({
                'correct': False,
                'game_over': True,
                'movie_title': movie.title,
                'attempts_left': 0,
                'message': f'Game Over! The movie was: {movie.title}'
            })
        
        # Calculate num_guesses (0-7, since first trivia was shown immediately)
        num_guesses = 8 - game_state['attempts_left']
        
        # Generate new trivia
        trivia_result = generate_trivia(movie, num_guesses, game_state.get('used_trivia', []))
        
        # Update used_trivia
        if 'used_trivia' not in game_state:
            game_state['used_trivia'] = []
        game_state['used_trivia'].append(trivia_result.fact)
        
        # Update revealed_trivia with correct difficulty
        if 'revealed_trivia' not in game_state:
            game_state['revealed_trivia'] = []
            
        # Determine difficulty based on num_guesses
        if num_guesses < 2:  # First 2 guesses - Hard
            difficulty = 'H'
        elif num_guesses < 5:  # Next 3 guesses - Medium
            difficulty = 'M'
        else:  # Last 3 guesses - Easy
            difficulty = 'E'
            
        game_state['revealed_trivia'].append({
            'trivia_fact': trivia_result.fact,
            'difficulty': difficulty
        })
        request.session.modified = True
        
        return JsonResponse({
            'correct': False,
            'attempts_left': game_state['attempts_left'],
            'new_trivia': trivia_result.fact
        })
        
    except Exception as e:
        print(f"Error in make_guess: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def game_over(request):
    """Show game results and option to start new game"""
    game_state = request.session.get('game_state', {})
    
    # If no game state or game not over, redirect to choose movie
    if not game_state:
        return redirect('choose_movie')
        
    movie = get_object_or_404(Movie, pk=game_state.get('movie_id'))
    
    context = {
        'won': game_state.get('won', False),
        'movie': movie,
        'attempts_used': 9 - game_state.get('attempts_left', 0),
        'score': game_state.get('score', 0)
    }
    
    # Clear game state after showing results
    if 'game_state' in request.session:
        del request.session['game_state']
    
    return render(request, "trivia_game/game_over.html", context)

def get_trivia_facts(movie):
    """
    Generate trivia facts for a movie.
    """
    facts = []
    
    print(f"\nGenerating trivia facts for movie: {movie.title}")
    
    hard_fact_options = []
    
    # Actor fact
    if movie.actors.exists():
        actor_names = ', '.join([actor.name for actor in movie.actors.all()[:3]])
        hard_fact_options.append({
            'text': f"The movie stars {actor_names}", 
            'difficulty': 'hard'
        })
    
    # IMDB rating fact
    hard_fact_options.append({
        'text': f"This movie has an IMDB rating of {movie.imdb_rating}", 
        'difficulty': 'hard'
    })
    
    # Studio fact
    if movie.studio:
        hard_fact_options.append({
            'text': f"This movie was produced by {movie.studio.name}", 
            'difficulty': 'hard'
        })
    
    print(f"Total hard facts available: {len(hard_fact_options)}")
    # Always take exactly 3 hard facts or all available if less than 3
    hard_facts = random.sample(hard_fact_options, min(3, len(hard_fact_options)))
    print(f"Selected hard facts: {len(hard_facts)}")
    for fact in hard_facts:
        print(f"- {fact['text']}")
    
    # Add medium facts (pick 3 max)
    medium_fact_options = []
    
    # Director fact
    if movie.director:
        medium_fact_options.append({
            'text': f"The director is {movie.director.name}", 
            'difficulty': 'medium'
        })
    
    # Genre fact
    medium_fact_options.append({
        'text': f"The movie's genre is {movie.genre}", 
            'difficulty': 'medium'
        })
    
    # Release date fact
    medium_fact_options.append({
        'text': f"This movie was released in {movie.release_date}", 
        'difficulty': 'medium'
    })
    
    print(f"\nTotal medium facts available: {len(medium_fact_options)}")
    # Always take exactly 3 medium facts or all available if less than 3
    medium_facts = random.sample(medium_fact_options, min(3, len(medium_fact_options)))
    print(f"Selected medium facts: {len(medium_facts)}")
    for fact in medium_facts:
        print(f"- {fact['text']}")
    
    # Add easy facts (pick 3 max)
    easy_fact_options = [
        {'text': f"This is a {movie.genre} movie", 'difficulty': 'easy'},
        {'text': f"The movie was made in the {str(movie.release_date)[:3]}0s", 'difficulty': 'easy'},
    ]
    
    print(f"\nTotal easy facts available: {len(easy_fact_options)}")
    print("Easy facts:")
    for fact in easy_fact_options:
        print(f"- {fact['text']}")
    
    # Clear the facts list and add exactly what we want
    facts = []
    facts.extend(hard_facts[:3])    # Ensure exactly 3 hard facts
    facts.extend(medium_facts[:3])  # Ensure exactly 3 medium facts
    facts.extend(easy_fact_options[:3])  # Ensure exactly 3 easy facts
    
    print(f"\nTotal facts added: {len(facts)}")
    print("Final facts list:")
    for i, fact in enumerate(facts):
        print(f"{i+1}. ({fact['difficulty']}) {fact['text']}")
    
    return facts

def calculate_score_multiplier(trivia_quality, num_guesses):
    """Calculate score multiplier based on trivia quality and guess number.
    
    Args:
        trivia_quality (TriviaQuality): Quality level of the trivia
        num_guesses (int): Number of guesses made so far
        
    Returns:
        float: Score multiplier
    """
    # Base multiplier from difficulty level
    base_multiplier = 3 if num_guesses < 3 else (2 if num_guesses < 6 else 1)
    
    # Quality adjustment
    quality_multiplier = {
        TriviaQuality.HIGH: 1.2,    # Bonus for database trivia
        TriviaQuality.MEDIUM: 1.0,  # Standard for direct attributes
        TriviaQuality.LOW: 0.8      # Penalty for fallback trivia
    }.get(trivia_quality, 1.0)
    
    return base_multiplier * quality_multiplier

def calculate_score(movie, num_guesses, trivia_quality=TriviaQuality.MEDIUM):
    """Calculate score based on remaining guesses and trivia quality.
    
    Args:
        movie (Movie): The movie object
        num_guesses (int): Number of guesses made so far
        trivia_quality (TriviaQuality): Quality level of the trivia
        
    Returns:
        int: Score
    """
    try:
        remaining_guesses = 9 - num_guesses
        if remaining_guesses <= 0:
            return 0
            
        # Base points for each difficulty level
        base_points = {
            'easy': 5,    # Guesses 7-9
            'medium': 10, # Guesses 4-6
            'hard': 15    # Guesses 1-3
        }
        
        # Calculate points for each remaining guess
        easy_remaining = min(max(0, remaining_guesses - 6), 3) * base_points['easy']
        medium_remaining = min(max(0, remaining_guesses - 3), 3) * base_points['medium']
        hard_remaining = min(remaining_guesses, 3) * base_points['hard']
        
        # Calculate base score
        base_score = easy_remaining + medium_remaining + hard_remaining
        
        # Apply quality multiplier
        quality_multiplier = {
            TriviaQuality.HIGH: 1.2,   # 20% bonus for high-quality trivia
            TriviaQuality.MEDIUM: 1.0,  # Standard score for medium quality
            TriviaQuality.LOW: 0.8      # 20% penalty for low-quality trivia
        }.get(trivia_quality, 1.0)
        
        return int(base_score * quality_multiplier)
        
    except Exception as e:
        return 0