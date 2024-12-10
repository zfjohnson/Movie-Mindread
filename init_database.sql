
CREATE TABLE trivia_game_studio (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address TEXT
);

CREATE TABLE trivia_game_director (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    debut_movie VARCHAR(200)
);

CREATE TABLE trivia_game_actor (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL
);

CREATE TABLE trivia_game_movie (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    release_date INTEGER NOT NULL CHECK (release_date >= 1888 AND release_date <= 2030),
    genre VARCHAR(100) NOT NULL,
    imdb_rating DECIMAL(3,1) NOT NULL CHECK (imdb_rating >= 0 AND imdb_rating <= 10),
    studio_id INTEGER REFERENCES trivia_game_studio(id) ON DELETE SET NULL,
    director_id INTEGER REFERENCES trivia_game_director(id) ON DELETE SET NULL
);

CREATE TABLE trivia_game_movie_actors (
    id SERIAL PRIMARY KEY,
    movie_id INTEGER REFERENCES trivia_game_movie(id) ON DELETE CASCADE,
    actor_id INTEGER REFERENCES trivia_game_actor(id) ON DELETE CASCADE
);

CREATE TABLE trivia_game_trivia (
    id SERIAL PRIMARY KEY,
    movie_id INTEGER REFERENCES trivia_game_movie(id) ON DELETE CASCADE,
    trivia_fact TEXT NOT NULL,
    difficulty VARCHAR(1) CHECK (difficulty IN ('E', 'M', 'H')),
);
