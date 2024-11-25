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
        game_state['attempts_left'] -= 1
        if is_correct:
            game_state['game_over'] = True
            game_state['won'] = True
            request.session.modified = True
            return JsonResponse({
                'correct': True,
                'message': f'Congratulations! You correctly guessed the movie: {movie.title}',
                'movie_title': movie.title
            })
        
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