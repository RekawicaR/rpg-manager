from django.db import models


class Source(models.Model):
    '''A book or other extension that is a source of new character options and other game content.'''

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
