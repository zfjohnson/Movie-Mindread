from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import Movie, Trivia
from django.db.models import Q
import random
import json

def index(request):
    # Clear any existing game state
    if 'game_state' in request.session:
        del request.session['game_state']
    return render(request, "index.html")

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

def start_game(request, movie_id):
    """Transition from chooser to guesser phase"""
    movie = get_object_or_404(Movie, pk=movie_id)
    
    # Get all trivia for the movie and sort by difficulty
    trivia_facts = list(Trivia.objects.filter(movie=movie))
    
    # Shuffle trivia within each difficulty level
    easy_trivia = [t for t in trivia_facts if t.difficulty == 'E']
    medium_trivia = [t for t in trivia_facts if t.difficulty == 'M']
    hard_trivia = [t for t in trivia_facts if t.difficulty == 'H']
    
    random.shuffle(easy_trivia)
    random.shuffle(medium_trivia)
    random.shuffle(hard_trivia)
    
    # Store game state in session
    request.session['game_state'] = {
        'movie_id': movie_id,
        'attempts_left': 9,
        'revealed_trivia': [],
        'available_trivia': [t.id for t in hard_trivia + medium_trivia + easy_trivia],
        'game_over': False,
        'phase': 'guesser'
    }
    
    return redirect('play_game')

def play_game(request):
    """Second phase: Guesser tries to identify the movie"""
    game_state = request.session.get('game_state')
    
    if not game_state or game_state.get('phase') != 'guesser':
        return redirect('choose_movie')
    
    # Get the current trivia facts that have been revealed
    revealed_trivia = []
    for trivia_id in game_state['revealed_trivia']:
        trivia = get_object_or_404(Trivia, pk=trivia_id)
        revealed_trivia.append(trivia)
    
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
        if len(game_state.get('revealed_trivia', [])) < len(game_state.get('available_trivia', [])):
            next_trivia_id = game_state['available_trivia'][len(game_state['revealed_trivia'])]
            game_state['revealed_trivia'].append(next_trivia_id)
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