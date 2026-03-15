from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    class GlobalRole(models.TextChoices):
        USER = "USER"
        MODERATOR = "MODERATOR"

    role = models.CharField(
        max_length=20,
        choices=GlobalRole.choices,
        default=GlobalRole.USER
    )
