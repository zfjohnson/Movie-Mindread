from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

<<<<<<< HEAD
class Director(models.Model):
    director_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)
    debut_movie = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Studio(models.Model):
    studio_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)
    address = models.CharField(max_length=255)
=======
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
>>>>>>> sqlite-version

    def __str__(self):
        return self.name

class Movie(models.Model):
<<<<<<< HEAD
    movie_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, null=False)
    month = models.CharField(max_length=255)
    day = models.IntegerField()
    year = models.IntegerField()
    director = models.ForeignKey(Director, on_delete=models.CASCADE)
    studios = models.ManyToManyField(Studio, through='FilmedBy')
=======
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
>>>>>>> sqlite-version

    def __str__(self):
        return self.title

<<<<<<< HEAD
class Actor(models.Model):
    actor_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)
    movies = models.ManyToManyField(Movie, through='Casts')

    def __str__(self):
        return self.name

class Genre(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    type = models.CharField(max_length=255)

    class Meta:
        unique_together = ('movie', 'type')

class ProductionCompany(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('movie', 'company_name')

class FilmedBy(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    studio = models.ForeignKey(Studio, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('movie', 'studio')

class Casts(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('movie', 'actor')

class Trivia(models.Model):
    trivia_id = models.AutoField(primary_key=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    trivia_fact = models.TextField(null=False)

    class Meta:
        abstract = True

class EasyTrivia(Trivia):
    pass

class MediumTrivia(Trivia):
    pass

class HardTrivia(Trivia):
    pass
=======
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
>>>>>>> sqlite-version
