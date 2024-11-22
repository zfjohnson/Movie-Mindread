document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('guess-form');
    const submitButton = document.getElementById('submit-guess');
    let isSubmitting = false;

    if (form) {
        // Remove any existing event listeners
        const newForm = form.cloneNode(true);
        form.parentNode.replaceChild(newForm, form);
        
        newForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Prevent multiple submissions
            if (isSubmitting) {
                console.log('Submission already in progress');
                return;
            }
            
            isSubmitting = true;
            submitButton.disabled = true;
            
            try {
                const formData = new FormData(this);
                const response = await fetch(guessUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                const messageDiv = document.getElementById('message');
                
                if (data.error) {
                    messageDiv.className = 'alert alert-danger';
                    messageDiv.textContent = data.error;
                    messageDiv.style.display = 'block';
                    return;
                }
                
                if (data.correct) {
                    messageDiv.className = 'alert alert-success';
                    messageDiv.textContent = data.message;
                    messageDiv.style.display = 'block';
                    setTimeout(() => {
                        window.location.href = gameOverUrl;
                    }, 1500);
                } else {
                    if (data.game_over) {
                        messageDiv.className = 'alert alert-danger';
                        messageDiv.textContent = `Game Over! The movie was: ${data.movie_title}`;
                        messageDiv.style.display = 'block';
                        setTimeout(() => {
                            window.location.href = gameOverUrl;
                        }, 1500);
                    } else {
                        messageDiv.className = 'alert alert-warning';
                        messageDiv.textContent = 'Incorrect guess. Try again!';
                        messageDiv.style.display = 'block';
                        
                        // Update attempts and progress bar
                        document.getElementById('attempts-left').textContent = data.attempts_left;
                        const progressBar = document.querySelector('.progress-bar');
                        progressBar.style.width = `${data.progress_percentage}%`;
                        progressBar.setAttribute('aria-valuenow', data.attempts_left);
                        
                        // Reload to show new trivia
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    }
                }
                
            } catch (error) {
                console.error('Error:', error);
                const messageDiv = document.getElementById('message');
                messageDiv.className = 'alert alert-danger';
                messageDiv.textContent = 'An error occurred. Please try again.';
                messageDiv.style.display = 'block';
            } finally {
                // Only reset submission state if we're not redirecting
                if (!isSubmitting) {
                    submitButton.disabled = false;
                }
            }
        });
    }
});
