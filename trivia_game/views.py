"""
Movie Mindread Game Views

This module contains all the view functions and helper classes for the Movie Mindread game.
The game allows one player to choose a movie while another player tries to guess it
through a series of trivia-based hints.

Key Components:
- Movie selection and search functionality
- Trivia generation with quality tracking
- Game state management
- Score calculation
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.core.exceptions import ValidationError
import random
from .models import Movie, Actor, Studio, Director, EasyTrivia, MediumTrivia, HardTrivia

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
    """Game entry point view.
    
    Resets game state and displays the initial game page where players
    choose their roles (movie chooser or guesser).
    """
    try:
        request.session.flush()  # Clear all session data
        request.session['num_guesses'] = 0
        request.session['chosen_movie_id'] = None
        request.session['guesses'] = []
        return render(request, "trivia_game/index.html")
    except Exception as e:
        messages.error(request, 'Error resetting game state. Please try again.')
        return render(request, "trivia_game/index.html", status=500)

@ensure_csrf_cookie
def choose_movie(request):
    """Movie selection view for the chooser.
    
    Displays the movie search interface where the choosing player can
    search for and select a movie for the game.
    """
    try:
        # Clear any existing game state
        request.session['num_guesses'] = 0
        request.session['guesses'] = []
        return render(request, "trivia_game/choose_movie.html")
    except Exception as e:
        messages.error(request, 'Error loading movie selection. Please try again.')
        return redirect('trivia_game:index')

@ensure_csrf_cookie
def guess_movie(request):
    """Movie guessing view for the guesser.
    
    Displays the guessing interface where the guessing player can
    make guesses about the chosen movie.
    """
    try:
        if 'chosen_movie_id' not in request.session:
            messages.error(request, 'No movie has been chosen yet!')
            return redirect('trivia_game:index')
        
        # Validate chosen_movie_id exists in database
        movie_id = request.session.get('chosen_movie_id')
        try:
            Movie.objects.get(movie_id=movie_id)
        except Movie.DoesNotExist:
            messages.error(request, 'The chosen movie no longer exists!')
            return redirect('trivia_game:index')
            
        return render(request, "trivia_game/guess_movie.html")
    except Exception as e:
        messages.error(request, 'Error loading guessing interface. Please try again.')
        return redirect('trivia_game:index')

def wait_for_guesses(request):
    """Waiting view for the chooser.
    
    Displays a waiting screen for the chooser while the guesser makes
    guesses about the chosen movie.
    """
    try:
        chosen_movie_id = request.session.get('chosen_movie_id')
        if not chosen_movie_id:
            messages.error(request, 'You need to choose a movie first!')
            return redirect('trivia_game:choose_movie')
        
        try:
            movie = Movie.objects.get(movie_id=chosen_movie_id)
        except Movie.DoesNotExist:
            messages.error(request, 'The chosen movie no longer exists!')
            return redirect('trivia_game:choose_movie')
            
        return render(request, "trivia_game/wait_for_guesses.html", {'movie': movie})
    except Exception as e:
        messages.error(request, 'Error loading waiting screen. Please try again.')
        return redirect('trivia_game:index')

def get_guesses(request):
    """API endpoint to retrieve the current game state.
    
    Returns the current number of guesses, game over status, and
    the list of guesses made so far.
    
    Returns:
        JsonResponse: Game state data
    """
    try:
        if 'chosen_movie_id' not in request.session:
            return JsonResponse({'error': 'No active game session'}, status=400)
            
        guesses = request.session.get('guesses', [])
        game_over = request.session.get('num_guesses', 0) >= 9
        return JsonResponse({
            'guesses': guesses,
            'game_over': game_over
        })
    except Exception as e:
        return JsonResponse({'error': 'Error retrieving guesses'}, status=500)

def search_movie(request):
    """API endpoint for movie search functionality.
    
    Searches across multiple fields:
    - Movie title
    - Release year
    - Director name
    - Genre
    
    Returns:
        JsonResponse: List of matching movies with basic details
    """
    try:
        query = request.GET.get('query', '').strip()
        if not query:
            return JsonResponse({'movies': []})
            
        # Limit query length for security
        query = query[:100]
        
        # Search across multiple fields
        movies = Movie.objects.filter(
            Q(title__icontains=query) |
            Q(year__icontains=query) |
            Q(director__name__icontains=query) |
            Q(genre__type__icontains=query)
        ).distinct()[:20]  # Limit results and remove duplicates
        
        # Format response with additional details
        movie_list = []
        for movie in movies:
            movie_list.append({
                'movie_id': movie.movie_id,
                'title': movie.title,
                'year': movie.year,
                'director': movie.director.name if movie.director else None,
                'genres': [g.type for g in movie.genre_set.all()]
            })
            
        return JsonResponse({
            'movies': movie_list,
            'total_count': len(movie_list)
        })
    except Exception as e:
        return JsonResponse({
            'error': 'Error searching movies',
            'message': str(e)
        }, status=500)

def get_movie(request, movie_id):
    """API endpoint to retrieve detailed movie information.
    
    Args:
        movie_id (int): The ID of the movie to retrieve
        
    Returns:
        JsonResponse: Detailed movie information including related data
    """
    try:
        if not isinstance(movie_id, int) or movie_id < 1:
            return JsonResponse({'error': 'Invalid movie ID'}, status=400)
            
        movie = get_object_or_404(Movie, movie_id=movie_id)
        
        # Get all related information
        actors = [{'id': a.actor_id, 'name': a.name} 
                 for a in movie.actor_set.all()[:5]]  # Limit to top 5 actors
                 
        studios = [{'id': s.studio_id, 'name': s.name} 
                  for s in movie.studios.all()]
                  
        genres = [{'id': g.genre_id, 'type': g.type} 
                 for g in movie.genre_set.all()]
        
        return JsonResponse({
            'id': movie.movie_id,
            'title': movie.title,
            'year': movie.year,
            'director': movie.director.name if movie.director else None,
            'actors': actors,
            'studios': studios,
            'genres': [g['type'] for g in genres]
        })
    except Movie.DoesNotExist:
        return JsonResponse({'error': 'Movie not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Error retrieving movie'}, status=500)

def set_movie(request, movie_id):
    """API endpoint to set the chosen movie.
    
    Args:
        movie_id (int): The ID of the movie to set as chosen
        
    Returns:
        JsonResponse: Success status
    """
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
        if not isinstance(movie_id, int) or movie_id < 1:
            return JsonResponse({'error': 'Invalid movie ID'}, status=400)
            
        # Verify movie exists
        try:
            Movie.objects.get(movie_id=movie_id)
        except Movie.DoesNotExist:
            return JsonResponse({'error': 'Movie not found'}, status=404)
            
        request.session['chosen_movie_id'] = movie_id
        request.session['num_guesses'] = 0
        request.session['guesses'] = []
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': 'Error setting movie'}, status=500)

def make_guess(request):
    """API endpoint to make a guess.
    
    Args:
        guess (str): The text of the guess
        
    Returns:
        JsonResponse: Result of the guess (correct, incorrect, or game over)
    """
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        guess = request.POST.get('guess', '').strip()
        if not guess:
            return JsonResponse({'error': 'No guess provided'}, status=400)
            
        # Limit guess length for security
        guess = guess[:255]
        
        num_guesses = request.session.get('num_guesses', 0)
        chosen_movie_id = request.session.get('chosen_movie_id')
        
        if not chosen_movie_id:
            return JsonResponse({'error': 'No movie chosen'}, status=400)
            
        try:
            movie = Movie.objects.get(movie_id=chosen_movie_id)
        except Movie.DoesNotExist:
            return JsonResponse({'error': 'Chosen movie no longer exists'}, status=404)
            
        if num_guesses >= 9:
            return JsonResponse({'error': 'Maximum guesses reached'}, status=400)
            
        num_guesses += 1
        request.session['num_guesses'] = num_guesses
        
        # Store guess in session
        guesses = request.session.get('guesses', [])
        guesses.append({'number': num_guesses, 'text': guess})
        request.session['guesses'] = guesses
        
        if movie.title.lower() == guess.lower():
            score = calculate_score(movie, num_guesses)
            return JsonResponse({
                'status': 'correct',
                'score': score,
                'num_guesses': num_guesses
            })
        
        if num_guesses >= 9:
            return JsonResponse({
                'status': 'game_over',
                'correct_movie': movie.title
            })
        
        trivia_result = generate_trivia(movie, num_guesses)
        return JsonResponse({
            'status': 'incorrect',
            'trivia': trivia_result.fact,
            'num_guesses': num_guesses,
            'trivia_quality': trivia_result.quality,
            'trivia_source': trivia_result.source
        })
    except Exception as e:
        return JsonResponse({'error': 'Error processing guess'}, status=500)

def generate_trivia(movie, num_guesses):
    """Generate trivia for a movie based on the number of guesses.
    
    Args:
        movie (Movie): The movie object to generate trivia for
        num_guesses (int): Number of guesses made so far
        
    Returns:
        TriviaResult: A trivia fact with metadata about its quality
    """
    try:
        # Validate inputs
        if not movie:
            return TriviaResult("Error: No movie provided", TriviaQuality.LOW, "error")
        if not isinstance(num_guesses, int) or num_guesses < 0 or num_guesses > 9:
            return TriviaResult("Error: Invalid number of guesses", TriviaQuality.LOW, "error")

        # Define difficulty levels
        if num_guesses < 3:  # Hard
            trivia_result = generate_hard_trivia(movie)
        elif num_guesses < 6:  # Medium
            trivia_result = generate_medium_trivia(movie)
        else:  # Easy
            trivia_result = generate_easy_trivia(movie)
            
        # Adjust score multiplier based on trivia quality
        trivia_result.score_multiplier = calculate_score_multiplier(trivia_result.quality, num_guesses)
        return trivia_result
            
    except Exception as e:
        return TriviaResult("An unexpected error occurred while generating trivia", 
                          TriviaQuality.LOW, "error")

def generate_hard_trivia(movie):
    """Generate hard difficulty trivia.
    
    Returns:
        TriviaResult: A trivia fact with metadata about its quality
    """
    try:
        # Try to get a hard trivia fact from database first
        hard_trivia = HardTrivia.objects.filter(movie=movie).order_by('?').first()
        if hard_trivia:
            return TriviaResult(hard_trivia.trivia_fact, TriviaQuality.HIGH, "database")

        # Fallback to actor/studio facts if no database trivia
        actor_facts = []
        studio_facts = []
        
        # Get actor facts with error handling
        try:
            actors = movie.actor_set.all()
            if actors:
                actor_facts = [
                    {'fact': f"This movie stars {a.name}", 'source': 'actor'}
                    for a in actors
                ]
        except Exception:
            pass
            
        # Get studio facts with error handling
        try:
            studios = movie.studios.all()
            if studios:
                studio_facts = [
                    {'fact': f"This movie was filmed by {s.name}", 'source': 'studio'}
                    for s in studios
                ]
        except Exception:
            pass
            
        # Combine all available facts
        all_facts = actor_facts + studio_facts
        
        if all_facts:
            chosen = random.choice(all_facts)
            return TriviaResult(chosen['fact'], TriviaQuality.MEDIUM, chosen['source'])
            
        # Ultimate fallback if no facts available
        return TriviaResult(f"This is a challenging movie from {movie.year}", 
                          TriviaQuality.LOW, "year")
        
    except Exception as e:
        return TriviaResult("Unable to generate hard trivia at this time",
                          TriviaQuality.LOW, "error")

def generate_medium_trivia(movie):
    """Generate medium difficulty trivia.
    
    Returns:
        TriviaResult: A trivia fact with metadata about its quality
    """
    try:
        # Try to get a medium trivia fact from database first
        medium_trivia = MediumTrivia.objects.filter(movie=movie).order_by('?').first()
        if medium_trivia:
            return TriviaResult(medium_trivia.trivia_fact, TriviaQuality.HIGH, "database")

        # Prepare fallback facts
        fallback_facts = []
        
        # Try to get director info
        try:
            if movie.director and movie.director.name:
                fallback_facts.append(
                    {'fact': f"This movie was directed by {movie.director.name}",
                     'source': 'director'}
                )
        except Exception:
            pass
            
        # Try to get year info
        try:
            if movie.year:
                fallback_facts.append(
                    {'fact': f"This movie was released in {movie.year}",
                     'source': 'year'}
                )
        except Exception:
            pass
            
        if fallback_facts:
            chosen = random.choice(fallback_facts)
            return TriviaResult(chosen['fact'], TriviaQuality.MEDIUM, chosen['source'])
            
        # Ultimate fallback
        return TriviaResult("This is a moderately challenging movie to guess",
                          TriviaQuality.LOW, "generic")
        
    except Exception as e:
        return TriviaResult("Unable to generate medium trivia at this time",
                          TriviaQuality.LOW, "error")

def generate_easy_trivia(movie):
    """Generate easy difficulty trivia.
    
    Returns:
        TriviaResult: A trivia fact with metadata about its quality
    """
    try:
        # Try to get an easy trivia fact from database first
        easy_trivia = EasyTrivia.objects.filter(movie=movie).order_by('?').first()
        if easy_trivia:
            return TriviaResult(easy_trivia.trivia_fact, TriviaQuality.HIGH, "database")

        # Fallback to genre facts
        genre_facts = []
        
        try:
            genres = movie.genre_set.all()
            if genres:
                genre_facts = [
                    {'fact': f"This movie's genre is {g.type}", 'source': 'genre'}
                    for g in genres
                ]
        except Exception:
            pass
            
        if genre_facts:
            chosen = random.choice(genre_facts)
            return TriviaResult(chosen['fact'], TriviaQuality.MEDIUM, chosen['source'])
            
        # Ultimate fallback
        return TriviaResult("This should be an easy movie to guess",
                          TriviaQuality.LOW, "generic")
        
    except Exception as e:
        return TriviaResult("Unable to generate easy trivia at this time",
                          TriviaQuality.LOW, "error")

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