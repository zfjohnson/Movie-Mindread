from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .models import Movie, Trivia, Director, Studio
from django.db.models import Q
import random
import json

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
    """First phase: Chooser selects a movie"""
    # Clear any existing game state
    if 'game_state' in request.session:
        del request.session['game_state']
        
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


def start_game(request, movie_id):
    """Transition from chooser to guesser phase"""
    movie = get_object_or_404(Movie, pk=movie_id)
    
    # Get all database trivia for the movie and sort by difficulty
    db_trivia_facts = list(Trivia.objects.filter(movie=movie))
    
    # Generate additional trivia about movie details
    movie_detail_trivia = generate_movie_trivia(movie)
    
    # Combine database trivia with movie detail trivia
    all_trivia = []
    
    # Add database trivia
    for t in db_trivia_facts:
        all_trivia.append({
            'id': t.id,
            'fact': t.trivia_fact,
            'difficulty': t.difficulty,
            'is_db_trivia': True
        })
    
    # Add movie detail trivia
    for i, t in enumerate(movie_detail_trivia):
        all_trivia.append({
            'id': f'detail_{i}',
            'fact': t['fact'],
            'difficulty': t['difficulty'],
            'is_db_trivia': False
        })
    
    # Organize trivia by difficulty (exactly 3 of each)
    hard_trivia = [t for t in all_trivia if t['difficulty'] == 'H'][:3]
    medium_trivia = [t for t in all_trivia if t['difficulty'] == 'M'][:3]
    easy_trivia = [t for t in all_trivia if t['difficulty'] == 'E'][:3]
    
    # Ensure we have exactly 3 of each difficulty
    while len(hard_trivia) < 3:
        hard_trivia.append({
            'id': f'padding_hard_{len(hard_trivia)}',
            'fact': f'This is a challenging movie to guess',
            'difficulty': 'H',
            'is_db_trivia': False
        })
    
    while len(medium_trivia) < 3:
        medium_trivia.append({
            'id': f'padding_medium_{len(medium_trivia)}',
            'fact': f'This movie has moderate recognition',
            'difficulty': 'M',
            'is_db_trivia': False
        })
    
    while len(easy_trivia) < 3:
        easy_trivia.append({
            'id': f'padding_easy_{len(easy_trivia)}',
            'fact': f'This movie exists in our database',
            'difficulty': 'E',
            'is_db_trivia': False
        })
    
    # Shuffle within each difficulty level
    random.shuffle(hard_trivia)
    random.shuffle(medium_trivia)
    random.shuffle(easy_trivia)
    
    # Combine all trivia in strict order (3 hard -> 3 medium -> 3 easy)
    ordered_trivia = hard_trivia[:3] + medium_trivia[:3] + easy_trivia[:3]
    
    # Store game state in session
    game_state = {
        'movie_id': movie_id,
        'attempts_left': 9,
        'revealed_trivia': [ordered_trivia[0]],  # Start with first trivia revealed
        'available_trivia': ordered_trivia,
        'game_over': False,
        'phase': 'guesser'
    }
    request.session['game_state'] = game_state
    
    return redirect('play_game')

def play_game(request):
    """Second phase: Guesser tries to identify the movie"""
    game_state = request.session.get('game_state')
    
    if not game_state or game_state.get('phase') != 'guesser':
        return redirect('choose_movie')
    
    # Get the current trivia facts that have been revealed
    revealed_trivia = []
    for trivia in game_state['revealed_trivia']:
        if isinstance(trivia, dict):  # New format
            revealed_trivia.append({
                'fact': trivia['fact'],
                'difficulty': trivia['difficulty']
            })
        else:  # Old format (database ID)
            trivia_obj = get_object_or_404(Trivia, pk=trivia)
            revealed_trivia.append({
                'fact': trivia_obj.trivia_fact,
                'difficulty': trivia_obj.difficulty
            })
    
    # Calculate progress percentage
    progress_percentage = int((game_state['attempts_left'] / 9) * 100)
    
    return render(request, "trivia_game/play_game.html", {
        'attempts_left': game_state['attempts_left'],
        'revealed_trivia': revealed_trivia,
        'game_over': game_state['game_over'],
        'progress_percentage': progress_percentage
    })

@require_POST
def make_guess(request):
    """Handle a movie guess"""
    try:
        # Get the game state
        game_state = request.session.get('game_state')
        if not game_state:
            return JsonResponse({'error': 'No active game'}, status=400)

        # Get the guess from POST data
        guess = request.POST.get('guess', '').strip()
        
        if not guess:
            return JsonResponse({'error': 'No guess provided'}, status=400)

        # Get the correct movie
        movie = get_object_or_404(Movie, pk=game_state['movie_id'])
        
        # Check if the guess is correct (case-insensitive)
        is_correct = guess.lower() == movie.title.lower()
        
        if is_correct:
            game_state['game_over'] = True
            game_state['won'] = True
            request.session.modified = True
            return JsonResponse({
                'correct': True,
                'message': f'Congratulations! You correctly guessed the movie: {movie.title}',
                'movie_title': movie.title
            })
        
        # Handle incorrect guess
        game_state['attempts_left'] -= 1
        request.session.modified = True
        
        # Check if game is over due to no more attempts
        if game_state['attempts_left'] <= 0:
            game_state['game_over'] = True
            return JsonResponse({
                'correct': False,
                'game_over': True,
                'movie_title': movie.title,
                'attempts_left': 0,
                'progress_percentage': 0
            })
        
        # Reveal new trivia if available
        if len(game_state['revealed_trivia']) < len(game_state['available_trivia']):
            next_trivia = game_state['available_trivia'][len(game_state['revealed_trivia'])]
            game_state['revealed_trivia'].append(next_trivia)
            request.session.modified = True
        
        return JsonResponse({
            'correct': False,
            'game_over': False,
            'attempts_left': game_state['attempts_left'],
            'progress_percentage': int((game_state['attempts_left'] / 9) * 100)
        })
        
    except Exception as e:
        print(f"Error in make_guess: {str(e)}")  # Log the error
        return JsonResponse({'error': 'An error occurred'}, status=500)

def game_over(request):
    """Show game results and option to start new game"""
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

def generate_movie_trivia(movie):
    """Generate trivia facts about movie details"""
    hard_facts = []
    medium_facts = []
    easy_facts = []
    
    # HARD facts
    if movie.imdb_rating:
        hard_facts.append({
            'fact': f'This movie has an IMDb rating of {movie.imdb_rating}',
            'difficulty': 'H'
        })
    
    # Add more hard facts if needed
    hard_facts.append({
        'fact': f'This {movie.genre} movie was released by {movie.studio.name if movie.studio else "an unknown studio"} in {movie.release_date}',
        'difficulty': 'H'
    })
    
    # MEDIUM facts
    if movie.studio:
        medium_facts.append({
            'fact': f'This movie was produced by {movie.studio.name}',
            'difficulty': 'M'
        })
    
    if movie.release_date:
        medium_facts.append({
            'fact': f'This movie was released in {movie.release_date}',
            'difficulty': 'M'
        })
    
    actors = movie.actors.all()
    if actors:
        actor_names = ', '.join([actor.name for actor in actors[:3]])
        medium_facts.append({
            'fact': f'This movie stars {actor_names}',
            'difficulty': 'M'
        })
    
    # EASY facts
    if movie.director:
        easy_facts.append({
            'fact': f'This movie was directed by {movie.director.name}',
            'difficulty': 'E'
        })
    
    if movie.genre:
        easy_facts.append({
            'fact': f'This movie belongs to the {movie.genre} genre',
            'difficulty': 'E'
        })
    
    # Combine all facts ensuring we have at least 3 of each difficulty
    while len(hard_facts) < 3:
        hard_facts.append({
            'fact': f'This is a challenging movie to guess from {movie.release_date}',
            'difficulty': 'H'
        })
    
    while len(medium_facts) < 3:
        medium_facts.append({
            'fact': f'This movie was made in the {movie.release_date}s',
            'difficulty': 'M'
        })
    
    while len(easy_facts) < 3:
        easy_facts.append({
            'fact': f'This is a {movie.genre} movie',
            'difficulty': 'E'
        })
    
    # Return exactly 3 of each difficulty
    return (hard_facts[:3] + medium_facts[:3] + easy_facts[:3])