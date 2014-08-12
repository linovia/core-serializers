
from django.db import models


class BasicModel(models.Model):
    name = models.CharField(max_length=10)
