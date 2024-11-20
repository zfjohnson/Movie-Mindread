# Movie Mindread 🎬

A two-player movie trivia game where one player chooses a movie and the other tries to guess it through a series of trivia-based hints.

## Features 🌟

- Interactive movie search and selection
- Multi-level trivia system (Easy, Medium, Hard)
- Dynamic scoring based on trivia quality and remaining guesses
- Real-time game state updates
- Comprehensive movie database
- Beautiful, responsive UI

## Prerequisites 📋

- Python 3.10 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation 🚀

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Movie-Mindread.git
cd Movie-Mindread
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/MacOS
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the database:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser (for admin access):
```bash
python manage.py createsuperuser
```

6. Populate the database with sample data:
```bash
python manage.py populate_data
```

## Running the Application 🎮

1. Start the development server:
```bash
python manage.py runserver
```

2. Open your browser and navigate to:
   - Game: http://localhost:8000/trivia_game/
   - Admin interface: http://localhost:8000/admin/

## How to Play 🎲

### Player 1 (Movie Chooser):
1. Click "Choose a Movie" on the home page
2. Use the search bar to find a movie
3. Select a movie from the search results
4. Confirm your selection
5. Wait for Player 2 to make their guesses

### Player 2 (Guesser):
1. Click "Guess the Movie" on the home page
2. You have 9 attempts to guess the movie
3. Each wrong guess reveals a new trivia fact
4. Trivia facts get progressively more specific
5. Try to guess the movie with as few attempts as possible

## Scoring System 💯

- Base score starts at 1000 points
- Score decreases with each guess
- Multipliers based on:
  * Number of guesses used (3x, 2x, 1x)
  * Trivia quality (High: 1.5x, Medium: 1.2x, Low: 1.0x)
- Bonus points for quick guesses
- No points awarded after 9 guesses

## Database Structure 📊

The game uses several interconnected models:
- Movies
- Directors
- Studios
- Actors
- Genres
- Trivia (Easy/Medium/Hard)

## Development 🛠️

### Project Structure
```
Movie-Mindread/
├── manage.py
├── requirements.txt
├── README.md
├── movie_mindread/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── trivia_game/
    ├── management/
    │   └── commands/
    │       └── populate_data.py
    ├── migrations/
    ├── static/
    ├── templates/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── urls.py
    └── views.py
```

### Key Files
- `settings.py`: Main Django configuration
- `views.py`: Game logic and request handling
- `models.py`: Database models
- `populate_data.py`: Sample data generation

## Testing 🧪

Run the test suite:
```bash
python manage.py test
```

## Production Deployment 🚀

For production deployment:
1. Set `DEBUG = False` in settings.py
2. Configure a production-ready database
3. Set up static file serving
4. Use a production web server (e.g., Gunicorn)
5. Set up HTTPS
6. Configure proper security settings

## Security Considerations 🔒

- CSRF protection enabled
- SQL injection prevention
- XSS protection
- Secure session handling
- Input validation
- Error handling without exposing sensitive information

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Troubleshooting 🔧

### Common Issues:

1. Database Migration Issues:
```bash
python manage.py migrate --run-syncdb
```

2. Static Files Not Loading:
```bash
python manage.py collectstatic
```

3. Permission Issues:
- Check file permissions
- Verify database user permissions

4. Search Not Working:
- Ensure database is populated
- Check search query format

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments 👏

- Django Framework
- Bootstrap
- Movie data contributors
- Open source community

## Support 💬

For support:
1. Check the documentation
2. Search existing issues
3. Create a new issue
4. Contact the maintainers

---
Made with ❤️ by [Your Name]
