from django.db import models

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

    def __str__(self):
        return self.name

class Movie(models.Model):
    movie_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, null=False)
    month = models.CharField(max_length=255)
    day = models.IntegerField()
    year = models.IntegerField()
    director = models.ForeignKey(Director, on_delete=models.CASCADE)
    studios = models.ManyToManyField(Studio, through='FilmedBy')

    def __str__(self):
        return self.title

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
