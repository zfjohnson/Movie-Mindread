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

class ProductionCompany(models.Model):
    name = models.CharField(max_length=200)
    founding_year = models.IntegerField(null=True, blank=True)
    headquarters = models.CharField(max_length=200, blank=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='production_companies')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Production Companies"

class EasyTrivia(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='easy_trivia')
    trivia_fact = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Easy Trivia for {self.movie.title}"

    class Meta:
        verbose_name_plural = "Easy Trivia"
        ordering = ['created_at']

class MediumTrivia(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='medium_trivia')
    trivia_fact = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Medium Trivia for {self.movie.title}"

    class Meta:
        verbose_name_plural = "Medium Trivia"
        ordering = ['created_at']

class HardTrivia(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='hard_trivia')
    trivia_fact = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Hard Trivia for {self.movie.title}"

    class Meta:
        verbose_name_plural = "Hard Trivia"
        ordering = ['created_at']
