# Movie Mindread - Interactive Movie Trivia Game

A Django-based multiplayer movie guessing game where players test their movie knowledge through progressively revealing trivia facts.

## Features

- Progressive difficulty levels (Hard → Medium → Easy)
- Real-time movie data from IMDb
- Multiplayer support
- Dynamic trivia generation
- Score tracking system
- Comprehensive movie database

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git
- SQLite3

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Movie-Mindread.git
cd Movie-Mindread
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/MacOS
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python manage.py migrate
```

5. Load initial movie data:
```bash
python manage.py fetch_imdb_data
```
Note: Due to a current issue with the cinemagoerpackage itself, only the top 25 movies are able to be loaded. 
## Configuration

1. Create a `.env` file in the root directory with the following variables:
```env
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

2. Configure database settings in `movie_mindread/settings.py` if needed (SQLite is configured by default)

## Running the Server

1. Start the development server:
```bash
python manage.py runserver
```

2. Access the application at `http://localhost:8000`

## Game Rules

1. Each game consists of 9 trivia facts about a movie:
   - 3 Hard difficulty facts
   - 3 Medium difficulty facts
   - 3 Easy difficulty facts

2. Facts are revealed one at a time, starting with hard difficulty
3. Players can guess the movie at any time
4. Points are awarded based on:
   - How quickly the correct guess is made
   - How many trivia facts were revealed
   - The difficulty level of revealed facts

## Project Structure

- `trivia_game/` - Main application directory
  - `views.py` - Core game logic and views
  - `models.py` - Database models
  - `urls.py` - URL routing
  - `templates/` - HTML templates
  - `static/` - CSS, JavaScript, and images
  - `management/commands/` - Custom management commands
- `movie_mindread/` - Project settings directory
- `requirements.txt` - Project dependencies


## Testing

Run the test suite:
```bash
python manage.py test
```

## Troubleshooting

1. Database Issues:
   - Delete `db.sqlite3` and all migration files except `__init__.py`
   - Run `python manage.py makemigrations`
   - Run `python manage.py migrate`
   - Run `python manage.py fetch_imdb_data`

2. Package Issues:
   - Delete `venv` folder
   - Create new virtual environment
   - Reinstall requirements


## Authors

- Brayden Martin
- Zachary Johnson

## Acknowledgments

- IMDb for movie data
- Django Framework
- All contributors and testers