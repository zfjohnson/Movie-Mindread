from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q

from .models import Movie, Trivia, Director, Studio

import random
import json

class TrivaDif:
    HIGH = 3
    MEDIUM = 2
    LOW = 1   

class TriviaResult:
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
            
            return JsonResponse({
                'success': True,
                'movie': {
                    'id': movie.id,
                    'title': movie.title,
                    'release_date': movie.release_date,
                    'genre': movie.genre,
                    'imdb_rating': str(movie.imdb_rating),
                    'director': movie.director.name,
                    'studio': movie.studio.name
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
    # Clear any existing game state
    if 'game_state' in request.session:
        del request.session['game_state']
    
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
    movie = get_object_or_404(Movie, pk=movie_id)
    
    if request.method == 'POST':
        # Update movie details
        movie.title = request.POST.get('title')
        movie.release_date = request.POST.get('release_date')
        movie.genre = request.POST.get('genre')
        movie.imdb_rating = request.POST.get('imdb_rating')
        
        # Get or create director
        director_name = request.POST.get('director')
        director, created = Director.objects.get_or_create(name=director_name)
        movie.director = director
        
        # Get or create studio
        studio_name = request.POST.get('studio')
        studio, created = Studio.objects.get_or_create(name=studio_name)
        movie.studio = studio
        
        movie.save()
        return redirect('manage_movies')
    
    return render(request, "trivia_game/edit_movie.html", {
        'movie': movie
    })

def start_game(request, movie_id):
    try:
        movie = get_object_or_404(Movie, pk=movie_id)
        
        # Initialize game state
        game_state = {
            'movie_id': movie_id,
            'attempts_left': 9,
            'revealed_trivia': [],
            'won': False,
            'score': 0,
            'phase': 'guesser',
            'num_guesses': 0  # Start with 0 guesses
        }
        
        # Generate first trivia hint without counting it as a guess
        trivia_result = generate_hard_trivia(movie)  # Always start with a hard fact
        game_state['revealed_trivia'].append({
            'trivia_fact': trivia_result.fact,
            'difficulty': 'H', 
            'quality': trivia_result.quality
        })
        
        request.session['game_state'] = game_state
        
        # Redirect to play_game view
        return redirect('play_game')
        
    except Exception as e:
        print(f"Error in start_game: {str(e)}")
        return JsonResponse({'error': 'An error occurred'})

def play_game(request):
    game_state = request.session.get('game_state')
    
    # Get the movie object
    movie = get_object_or_404(Movie, pk=game_state['movie_id'])
    
    # Calculate progress percentage
    progress_percentage = int((game_state['attempts_left'] / 9) * 100)
    
    return render(request, "trivia_game/play_game.html", {
        'attempts_left': game_state['attempts_left'],
        'revealed_trivia': game_state.get('revealed_trivia', []),
        'game_over': game_state.get('game_over', False),
        'progress_percentage': progress_percentage
    })

@require_POST
def make_guess(request):
    try:
        game_state = request.session.get('game_state')

        # Get the guess from POST data
        guess = request.POST.get('guess', '').strip()
        
        if not guess:
            return JsonResponse({'error': 'No guess provided'})

        # Get the correct movie
        movie = get_object_or_404(Movie, pk=game_state['movie_id'])
        
        
        
        # Generate new trivia based on current number of guesses
        trivia_result = generate_trivia(movie, game_state['num_guesses'])
        
        # Check if the guess is correct (case-insensitive)
        is_correct = guess.lower() == movie.title.lower()
        
        if is_correct:
            score = calculate_score(movie, game_state['num_guesses'], trivia_result.quality)
            game_state['game_over'] = True
            game_state['won'] = True
            game_state['score'] = score
            request.session.modified = True
            return JsonResponse({
                'correct': True,
                'message': f'Congratulations! You correctly guessed the movie: {movie.title}',
                'movie_title': movie.title,
                'score': score
            })
        
        # Handle incorrect guess
        game_state['attempts_left'] -= 1
        
        # Add new trivia fact with proper difficulty based on number of guesses
        difficulty = 'H' if game_state['num_guesses'] < 2 else ('M' if game_state['num_guesses'] < 5 else 'E')
        print(f"Adding trivia with difficulty: {difficulty} (guess #{game_state['num_guesses']})")
        
        game_state['revealed_trivia'].append({
            'trivia_fact': trivia_result.fact,
            'difficulty': difficulty,
            'quality': trivia_result.quality
        })
        
        # Increment number of guesses AFTER adding trivia
        game_state['num_guesses'] += 1
        
        request.session.modified = True
        
        # Check if game is over due to no more attempts
        if game_state['attempts_left'] <= 0:
            game_state['game_over'] = True
            game_state['won'] = False
            game_state['score'] = 0
            return JsonResponse({
                'correct': False,
                'game_over': True,
                'movie_title': movie.title,
                'attempts_left': 0,
                'progress_percentage': 0,
                'new_trivia': trivia_result.fact
            })
        
        return JsonResponse({
            'correct': False,
            'game_over': False,
            'attempts_left': game_state['attempts_left'],
            'progress_percentage': int((game_state['attempts_left'] / 9) * 100),
            'new_trivia': trivia_result.fact
        })
        
    except Exception as e:
        print(f"Error in make_guess: {str(e)}")  # Log the error
        return JsonResponse({'error': 'An error occurred'}, status=500)

def game_over(request):
    game_state = request.session.get('game_state')
    
    if not game_state or not game_state['game_over']:
        return redirect('choose_movie')
    
    movie = get_object_or_404(Movie, pk=game_state['movie_id'])
    
    # Clear game state
    del request.session['game_state']
    
    return render(request, "trivia_game/game_over.html", {
        'won': game_state.get('won', False),
        'movie': movie,
        'attempts_used': 9 - game_state['attempts_left']
    })


def generate_trivia(movie, num_guesses):
    try:
        # Validate inputs
        if not movie:
            return TriviaResult("Error: No movie provided", "error")
        # First 3 guesses (first, 0, 1) get hard facts
        if num_guesses < 2:
            return generate_hard_trivia(movie)
            
        # Next 3 guesses (2, 3, 4) get medium facts
        elif num_guesses < 5:
            return generate_medium_trivia(movie)
            
        # Last 3 guesses (5, 6, 7, 8) get easy facts
        else:
            return generate_easy_trivia(movie)
            
    except Exception as e:
        print(f"Error in generate_trivia: {str(e)}")
        return TriviaResult("An unexpected error occurred while generating trivia", 
                          TrivaDif.LOW, "error")

def generate_hard_trivia(movie):
    try:
        print(f"Generating hard trivia for movie: {movie.title}")
        
        # Try to get a hard trivia fact from database first
        hard_trivia = Trivia.objects.filter(movie=movie).order_by('?').first()
        if hard_trivia:
            print(f"Found database trivia: {hard_trivia.trivia_fact}")
            return TriviaResult(hard_trivia.trivia_fact, TrivaDif.HIGH, "database")

        # Create a list of potential hard facts
        hard_facts = []
        
        # 1. Actor fact (combine all main actors)
        try:
            actors = movie.actors.all()[:3]  # Limit to 3 main actors
            if actors:
                actor_names = ', '.join(actor.name for actor in actors)
                hard_facts.append({
                    'fact': f"This movie stars {actor_names}",
                    'quality': TrivaDif.MEDIUM,
                    'source': 'actors'
                })
        except Exception as e:
            print(f"Error getting actors: {str(e)}")
        
        # 2. Studio fact
        try:
            if movie.studio:
                hard_facts.append({
                    'fact': f"This movie was produced by {movie.studio.name}",
                    'quality': TrivaDif.MEDIUM,
                    'source': 'studio'
                })
        except Exception as e:
            print(f"Error getting studio: {str(e)}")
        
        # 3. IMDB rating fact
        if hasattr(movie, 'imdb_rating') and movie.imdb_rating:
            hard_facts.append({
                'fact': f"This movie has an IMDB rating of {movie.imdb_rating}",
                'quality': TrivaDif.MEDIUM,
                'source': 'rating'
            })
        
        # If we have hard facts, randomly choose one
        if hard_facts:
            print(f"Found {len(hard_facts)} hard facts, selecting one randomly")
            chosen = random.choice(hard_facts)
            return TriviaResult(chosen['fact'], chosen['quality'], chosen['source'])
        
        # Fallback to a basic hard fact
        print("No specific hard facts found, using fallback")
        return TriviaResult(
            f"This movie was released in {movie.release_date}",
            TrivaDif.LOW,
            "fallback"
        )
        
    except Exception as e:
        print(f"Error in generate_hard_trivia: {str(e)}")
        return TriviaResult(
            "Unable to generate hard trivia at this time",
            TrivaDif.LOW,
            "error"
        )

def generate_medium_trivia(movie):
    """Generate medium difficulty trivia.
    
    Returns:
        TriviaResult: A trivia fact with metadata about its quality
    """
    try:
        print(f"Generating medium trivia for movie: {movie.title}")
        
        # Try to get a medium trivia fact from database first
        medium_trivia = Trivia.objects.filter(movie=movie).order_by('?').first()
        if medium_trivia:
            print(f"Found database trivia: {medium_trivia.trivia_fact}")
            return TriviaResult(medium_trivia.trivia_fact, TrivaDif.HIGH, "database")

        # Prepare fallback facts
        fallback_facts = []
        
        # Try to get director info
        try:
            print("Trying to get director...")
            if movie.director:
                print(f"Found director: {movie.director.name}")
                fallback_facts.append(
                    {'fact': f"This movie was directed by {movie.director.name}",
                     'source': 'director',
                     'quality': TrivaDif.MEDIUM
                    }
                )
        except Exception as e:
            print(f"Error getting director: {str(e)}")
            
        # Try to get year info
        try:
            print("Trying to get release date...")
            if movie.release_date:
                print(f"Found release date: {movie.release_date}")
                fallback_facts.append(
                    {'fact': f"This movie was released in {movie.release_date}",
                     'source': 'year',
                     'quality': TrivaDif.MEDIUM
                    }
                )
        except Exception as e:
            print(f"Error getting release date: {str(e)}")
            
        if fallback_facts:
            print(f"Found {len(fallback_facts)} fallback facts")
            chosen = random.choice(fallback_facts)
            return TriviaResult(chosen['fact'], chosen['quality'], chosen['source'])
            
        # Ultimate fallback
        print("No facts found, using generic fallback")
        return TriviaResult("This is a moderately challenging movie to guess",
                          TrivaDif.LOW, "generic")
        
    except Exception as e:
        print(f"Error in generate_medium_trivia: {str(e)}")
        return TriviaResult("Unable to generate medium trivia at this time",
                          TrivaDif.LOW, "error")

def generate_easy_trivia(movie):
    """Generate easy difficulty trivia.
    
    Returns:
        TriviaResult: A trivia fact with metadata about its quality
    """
    try:
        print(f"Generating easy trivia for movie: {movie.title}")
        
        # Try to get an easy trivia fact from database first
        easy_trivia = Trivia.objects.filter(movie=movie).order_by('?').first()
        if easy_trivia:
            print(f"Found database trivia: {easy_trivia.trivia_fact}")
            return TriviaResult(easy_trivia.trivia_fact, TrivaDif.HIGH, "database")

        # Fallback to genre facts
        genre_facts = []
        
        try:
            print("Trying to get genre...")
            if movie.genre:
                print(f"Found genre: {movie.genre}")
                genre_facts.append(
                    {'fact': f"This movie's genre is {movie.genre}", 
                     'source': 'genre',
                     'quality': TrivaDif.MEDIUM
                    }
                )
        except Exception as e:
            print(f"Error getting genre: {str(e)}")
            
        if genre_facts:
            print(f"Found {len(genre_facts)} genre facts")
            chosen = random.choice(genre_facts)
            return TriviaResult(chosen['fact'], chosen['quality'], chosen['source'])
            
        # Ultimate fallback
        print("No facts found, using generic fallback")
        return TriviaResult("This should be an easy movie to guess",
                          TrivaDif.LOW, "generic")
        
    except Exception as e:
        print(f"Error in generate_easy_trivia: {str(e)}")
        return TriviaResult("Unable to generate easy trivia at this time",
                          TrivaDif.LOW, "error")

def calculate_score_multiplier(trivia_quality, num_guesses):
    """Calculate score multiplier based on trivia quality and guess number.
    
    Args:
        trivia_quality (TrivaDif): Quality level of the trivia
        num_guesses (int): Number of guesses made so far
        
    Returns:
        float: Score multiplier
    """
    # Base multiplier from difficulty level
    base_multiplier = 3 if num_guesses < 3 else (2 if num_guesses < 6 else 1)
    
    # Quality adjustment
    quality_multiplier = {
        TrivaDif.HIGH: 1.2,    # Bonus for database trivia
        TrivaDif.MEDIUM: 1.0,  # Standard for direct attributes
        TrivaDif.LOW: 0.8      # Penalty for fallback trivia
    }.get(trivia_quality, 1.0)
    
    return base_multiplier * quality_multiplier

def calculate_score(movie, num_guesses, trivia_quality=TrivaDif.MEDIUM):
    """Calculate score based on remaining guesses and trivia quality.
    
    Args:
        movie (Movie): The movie object
        num_guesses (int): Number of guesses made so far
        trivia_quality (TrivaDif): Quality level of the trivia
        
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
            TrivaDif.HIGH: 1.2,   # 20% bonus for high-quality trivia
            TrivaDif.MEDIUM: 1.0,  # Standard score for medium quality
            TrivaDif.LOW: 0.8      # 20% penalty for low-quality trivia
        }.get(trivia_quality, 1.0)
        
        return int(base_score * quality_multiplier)
        
    except Exception as e:
        return 0

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