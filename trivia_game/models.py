from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Studio(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)  # Made optional

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Studios"

class Director(models.Model):
    name = models.CharField(max_length=200)
    debut_movie = models.CharField(max_length=200, blank=True)  # Made optional

    def __str__(self):
        return self.name

class Actor(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Movie(models.Model):
    title = models.CharField(max_length=200)
    release_date = models.IntegerField(
        validators=[
            MinValueValidator(1888),  # First movie ever made
            MaxValueValidator(2030)   # Future releases
        ]
    )
    genre = models.CharField(max_length=100)
    studio = models.ForeignKey(Studio, on_delete=models.SET_NULL, null=True, blank=True)
    director = models.ForeignKey(Director, on_delete=models.SET_NULL, null=True, blank=True)
    actors = models.ManyToManyField(Actor, related_name='movies', blank=True)
    imdb_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=1,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10)
        ]
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-release_date']

class Trivia(models.Model):
    DIFFICULTY_CHOICES = [
        ('E', 'Easy'),
        ('M', 'Medium'),
        ('H', 'Hard'),
    ]

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='trivia')
    trivia_fact = models.TextField()
    difficulty = models.CharField(max_length=1, choices=DIFFICULTY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_difficulty_display()} trivia for {self.movie.title}"

    class Meta:
        verbose_name_plural = "Trivia"
        ordering = ['difficulty', 'created_at']
