from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Movie, Director, Studio, Actor, Genre, EasyTrivia, MediumTrivia, HardTrivia
from django.core.exceptions import ValidationError
import json

class MovieMindreadTestCase(TestCase):
    def setUp(self):
        """Set up test data for all test methods."""
        self.client = Client()
        
        # Create test director
        self.director = Director.objects.create(
            name='Christopher Nolan',
            debut_movie='Following'
        )
        
        # Create test studio
        self.studio = Studio.objects.create(
            name='Warner Bros.',
            address='4000 Warner Blvd, Burbank, CA'
        )
        
        # Create test movie
        self.movie = Movie.objects.create(
            title='Inception',
            month='July',
            day=16,
            year=2010,
            director=self.director
        )
        self.movie.studios.add(self.studio)
        
        # Create test actor
        self.actor = Actor.objects.create(name='Leonardo DiCaprio')
        self.actor.movies.add(self.movie)
        
        # Create test genres
        self.genre1 = Genre.objects.create(movie=self.movie, type='Sci-Fi')
        self.genre2 = Genre.objects.create(movie=self.movie, type='Action')
        
        # Create test trivia
        self.easy_trivia = EasyTrivia.objects.create(
            movie=self.movie,
            trivia_fact="This movie was released in 2010"
        )
        self.medium_trivia = MediumTrivia.objects.create(
            movie=self.movie,
            trivia_fact="The movie's tagline was 'Your mind is the scene of the crime'"
        )
        self.hard_trivia = HardTrivia.objects.create(
            movie=self.movie,
            trivia_fact="The snow fortress sequence was filmed in Calgary"
        )

class ModelTests(MovieMindreadTestCase):
    """Test cases for model creation and validation."""
    
    def test_movie_creation(self):
        """Test that a movie can be created with valid data."""
        self.assertEqual(self.movie.title, 'Inception')
        self.assertEqual(self.movie.director.name, 'Christopher Nolan')
        self.assertEqual(self.movie.studios.first().name, 'Warner Bros.')
    
    def test_movie_str_representation(self):
        """Test the string representation of a movie."""
        expected_str = f"Inception (July 16, 2010)"
        self.assertEqual(str(self.movie), expected_str)
    
    def test_invalid_release_date(self):
        """Test that invalid release dates are rejected."""
        with self.assertRaises(ValidationError):
            Movie.objects.create(
                title='Invalid Movie',
                month='Invalid',
                day=50,
                year=2025,
                director=self.director
            )
    
    def test_director_movie_relationship(self):
        """Test the relationship between directors and movies."""
        self.assertEqual(self.director.movie_set.first(), self.movie)

class ViewTests(MovieMindreadTestCase):
    """Test cases for views."""
    
    def test_index_view(self):
        """Test the index view."""
        response = self.client.get(reverse('trivia_game:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'trivia_game/index.html')
    
    def test_movie_search(self):
        """Test the movie search functionality."""
        response = self.client.get(
            reverse('trivia_game:search_movies'),
            {'query': 'Inception'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue('movies' in data)
        self.assertEqual(len(data['movies']), 1)
        self.assertEqual(data['movies'][0]['title'], 'Inception')
    
    def test_movie_selection(self):
        """Test movie selection process."""
        response = self.client.post(
            reverse('trivia_game:select_movie'),
            {'movie_id': self.movie.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

class GameLogicTests(MovieMindreadTestCase):
    """Test cases for game logic."""
    
    def test_correct_guess(self):
        """Test handling of correct movie guess."""
        session = self.client.session
        session['selected_movie_id'] = self.movie.id
        session['remaining_guesses'] = 9
        session['current_score'] = 1000
        session.save()
        
        response = self.client.post(
            reverse('trivia_game:submit_guess'),
            {'guess': 'Inception'},
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertTrue(data['correct'])
        self.assertEqual(data['score'], 1000)
    
    def test_incorrect_guess(self):
        """Test handling of incorrect movie guess."""
        session = self.client.session
        session['selected_movie_id'] = self.movie.id
        session['remaining_guesses'] = 9
        session['current_score'] = 1000
        session.save()
        
        response = self.client.post(
            reverse('trivia_game:submit_guess'),
            {'guess': 'Wrong Movie'},
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertFalse(data['correct'])
        self.assertTrue('trivia' in data)
        self.assertEqual(data['remaining_guesses'], 8)
    
    def test_game_over_condition(self):
        """Test game over condition when guesses are exhausted."""
        session = self.client.session
        session['selected_movie_id'] = self.movie.id
        session['remaining_guesses'] = 1
        session['current_score'] = 100
        session.save()
        
        response = self.client.post(
            reverse('trivia_game:submit_guess'),
            {'guess': 'Wrong Movie'},
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertTrue(data['game_over'])

class TriviaTests(MovieMindreadTestCase):
    """Test cases for trivia functionality."""
    
    def test_trivia_difficulty_progression(self):
        """Test that trivia facts follow the correct difficulty progression."""
        session = self.client.session
        session['selected_movie_id'] = self.movie.id
        session['remaining_guesses'] = 9
        session.save()
        
        # First guess should return easy trivia
        response = self.client.post(
            reverse('trivia_game:submit_guess'),
            {'guess': 'Wrong Movie'},
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertEqual(data['trivia'], self.easy_trivia.trivia_fact)
        
        # After several guesses, should get medium trivia
        session['remaining_guesses'] = 6
        session.save()
        response = self.client.post(
            reverse('trivia_game:submit_guess'),
            {'guess': 'Wrong Movie'},
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertEqual(data['trivia'], self.medium_trivia.trivia_fact)
    
    def test_unique_trivia_facts(self):
        """Test that trivia facts are not repeated."""
        session = self.client.session
        session['selected_movie_id'] = self.movie.id
        session['remaining_guesses'] = 9
        session['revealed_trivia'] = []
        session.save()
        
        revealed_trivia = set()
        for _ in range(3):
            response = self.client.post(
                reverse('trivia_game:submit_guess'),
                {'guess': 'Wrong Movie'},
                content_type='application/json'
            )
            data = json.loads(response.content)
            self.assertNotIn(data['trivia'], revealed_trivia)
            revealed_trivia.add(data['trivia'])

class ScoreTests(MovieMindreadTestCase):
    """Test cases for scoring system."""
    
    def test_score_calculation(self):
        """Test the score calculation based on number of guesses."""
        session = self.client.session
        session['selected_movie_id'] = self.movie.id
        session['remaining_guesses'] = 9
        session['current_score'] = 1000
        session.save()
        
        # Score should decrease with each guess
        initial_score = 1000
        for i in range(3):
            response = self.client.post(
                reverse('trivia_game:submit_guess'),
                {'guess': 'Wrong Movie'},
                content_type='application/json'
            )
            data = json.loads(response.content)
            self.assertLess(data['score'], initial_score)
            initial_score = data['score']
    
    def test_final_score_multipliers(self):
        """Test score multipliers based on difficulty and remaining guesses."""
        session = self.client.session
        session['selected_movie_id'] = self.movie.id
        session['remaining_guesses'] = 8
        session['current_score'] = 1000
        session.save()
        
        response = self.client.post(
            reverse('trivia_game:submit_guess'),
            {'guess': 'Inception'},
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertEqual(data['score'], 1000 * 3)  # 3x multiplier for quick guess
