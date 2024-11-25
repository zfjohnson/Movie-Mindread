// Game State Management
let gameState = {
    currentScore: 1000,
    remainingGuesses: 9,
    selectedMovie: null,
    revealedTrivia: [],
    gameOver: false
};

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
    initializeGameElements();
    setupEventListeners();
});

function initializeGameElements() {
    // Initialize search functionality if on choose movie page
    const searchInput = document.getElementById('movie-search');
    if (searchInput) {
        setupMovieSearch();
    }

    // Initialize guess functionality if on guess page
    const guessForm = document.getElementById('guess-form');
    if (guessForm) {
        setupGuessForm();
    }
}

// Event Listeners Setup
function setupEventListeners() {
    // Setup navigation links
    const manageLink = document.getElementById('manage-link');
    if (manageLink) {
        manageLink.addEventListener('click', () => {
            window.location.href = '/manage/';
        });
    }

    // Setup new game button
    const newGameBtn = document.getElementById('new-game-btn');
    if (newGameBtn) {
        newGameBtn.addEventListener('click', startNewGame);
    }

    // Setup guess form submit
    const guessForm = document.getElementById('guess-form');
    if (guessForm) {
        guessForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const guessInput = document.getElementById('guess-input');
            submitGuess(guessInput.value);
            guessInput.value = '';
        });
    }
}

// Movie Search Functionality
function setupMovieSearch() {
    const searchInput = document.getElementById('movie-search');
    const movieList = document.getElementById('movie-list');

    searchInput.addEventListener('input', debounce(async (e) => {
        const searchTerm = e.target.value.trim();
        if (searchTerm.length < 2) {
            movieList.innerHTML = '';
            return;
        }

        try {
            const response = await fetch(`/trivia_game/search_movies/?query=${encodeURIComponent(searchTerm)}`);
            const data = await response.json();
            displayMovieResults(data.movies);
        } catch (error) {
            console.error('Error searching movies:', error);
            showMessage('Error searching movies. Please try again.', 'error');
        }
    }, 300));
}

function displayMovieResults(movies) {
    const movieList = document.getElementById('movie-list');
    movieList.innerHTML = '';

    movies.forEach(movie => {
        const movieItem = document.createElement('div');
        movieItem.className = 'movie-item';
        movieItem.innerHTML = `
            <h3>${movie.title} (${movie.year})</h3>
            <p>Director: ${movie.director}</p>
        `;
        movieItem.addEventListener('click', () => selectMovie(movie));
        movieList.appendChild(movieItem);
    });
}

function selectMovie(movie) {
    gameState.selectedMovie = movie;
    
    fetch('/trivia_game/select_movie/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ movie_id: movie.id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Movie selected successfully! Waiting for player 2...', 'success');
            window.location.href = '/trivia_game/wait_for_player/';
        } else {
            showMessage('Error selecting movie. Please try again.', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Error selecting movie. Please try again.', 'error');
    });
}

// Guess Functionality
function setupGuessForm() {
    const guessForm = document.getElementById('guess-form');
    const guessInput = document.getElementById('guess-input');

    guessForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const guess = guessInput.value.trim();
        
        if (!guess) {
            showMessage('Please enter a guess', 'error');
            return;
        }

        try {
            const response = await submitGuess(guess);
            handleGuessResponse(response);
            guessInput.value = '';
        } catch (error) {
            console.error('Error submitting guess:', error);
            showMessage('Error submitting guess. Please try again.', 'error');
        }
    });
}

async function submitGuess(guess) {
    const response = await fetch('/trivia_game/submit_guess/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ guess: guess })
    });
    return await response.json();
}

function handleGuessResponse(response) {
    if (response.correct) {
        handleCorrectGuess(response);
    } else {
        handleIncorrectGuess(response);
    }
    updateGameState(response);
}

function handleCorrectGuess(response) {
    showMessage('Congratulations! You guessed correctly!', 'success');
    gameState.gameOver = true;
    displayFinalScore(response.score);
    disableGuessing();
}

function handleIncorrectGuess(response) {
    showMessage('Incorrect guess. Try again!', 'error');
    displayNewTrivia(response.trivia);
    updateRemainingGuesses(response.remaining_guesses);
}

function updateGameState(response) {
    gameState.currentScore = response.score;
    gameState.remainingGuesses = response.remaining_guesses;
    updateScoreDisplay();
    
    if (response.game_over) {
        gameState.gameOver = true;
        handleGameOver(response);
    }
}

// UI Updates
function updateScoreDisplay() {
    const scoreElement = document.getElementById('current-score');
    if (scoreElement) {
        scoreElement.textContent = gameState.currentScore;
    }
}

function displayNewTrivia(trivia) {
    const triviaContainer = document.getElementById('trivia-container');
    if (triviaContainer && trivia) {
        const triviaElement = document.createElement('div');
        triviaElement.className = 'trivia-fact fade-in';
        triviaElement.textContent = trivia;
        triviaContainer.appendChild(triviaElement);
        gameState.revealedTrivia.push(trivia);
    }
}

function updateRemainingGuesses(remaining) {
    const guessesElement = document.getElementById('remaining-guesses');
    if (guessesElement) {
        guessesElement.textContent = remaining;
    }
}

function displayFinalScore(score) {
    const scoreContainer = document.getElementById('final-score-container');
    if (scoreContainer) {
        scoreContainer.innerHTML = `
            <h2>Final Score: ${score}</h2>
            <button class="btn btn-primary" onclick="startNewGame()">Play Again</button>
        `;
        scoreContainer.classList.add('fade-in');
    }
}

// Utility Functions
function showMessage(message, type) {
    const messageContainer = document.getElementById('message-container');
    if (messageContainer) {
        const messageElement = document.createElement('div');
        messageElement.className = `message message-${type} fade-in`;
        messageElement.textContent = message;
        messageContainer.innerHTML = '';
        messageContainer.appendChild(messageElement);
        
        // Auto-remove message after 5 seconds
        setTimeout(() => {
            messageElement.remove();
        }, 5000);
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function disableGuessing() {
    const guessForm = document.getElementById('guess-form');
    const guessInput = document.getElementById('guess-input');
    const submitButton = document.querySelector('#guess-form button');
    
    if (guessForm && guessInput && submitButton) {
        guessInput.disabled = true;
        submitButton.disabled = true;
    }
}

function startNewGame() {
    window.location.href = '/trivia_game/';
}

// Error Handling
window.onerror = function(msg, url, lineNo, columnNo, error) {
    console.error('Error: ', msg, '\nURL: ', url, '\nLine: ', lineNo, '\nColumn: ', columnNo, '\nError object: ', error);
    showMessage('An error occurred. Please refresh the page and try again.', 'error');
    return false;
};