from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Submission(models.Model):
    code = models.TextField()
    language = models.CharField(max_length=50)
    input_data = models.TextField(null = True,blank = True)
    output_data = models.TextField(null = True,blank = True)
