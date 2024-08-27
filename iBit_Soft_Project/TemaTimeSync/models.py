from django.db import models


# Create your models here.
class User(models.Model):
    first_name = models.CharField(max_length=125)
    last_name = models.CharField(max_length=125)
    username = models.CharField(max_length=120)
    email = models.CharField(max_length=120)
