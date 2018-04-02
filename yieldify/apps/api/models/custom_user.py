from django.db import models


class CustomUser(models.Model):
    user_id = models.CharField(max_length=64, unique=True)
