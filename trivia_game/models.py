from django.db import models

# Create your models here.

class Movie(models.Model):
    title = models.CharField(max_length=200)
    release_date = models.DateField()
    director = models.CharField(max_length=200)
    genre = models.CharField(max_length=200)
    imdb_rating = models.DecimalField(max_digits=3, decimal_places=1)
    studio = models.CharField(max_length=200)
    
    def __str__(self):
        return self.question_text
