from django.db import models


class TimeUnit(models.TextChoices):
    MINUTE = "MINUTE", "Minute"
    HOUR = "HOUR", "Hour"
    DAY = "DAY", "Day"


class DistanceUnit(models.TextChoices):
    FT = "FT", "Feet"
    MI = "MI", "Mile"


class AreaType(models.TextChoices):
    LINE = "LINE", "Line"
    CONE = "CONE", "Cone"
    CUBE = "CUBE", "Cube"
    SPHERE = "SPHERE", "Sphere"
    CYLINDER = "CYLINDER", "Cylinder"
    EMANATION = "EMANATION", "Emanation"


class MagicSchool(models.TextChoices):
    ABJURATION = "ABJ", "Abjuration"
    CONJURATION = "CONJ", "Conjuration"
    DIVINATION = "DIV", "Divination"
    ENCHANTMENT = "ENCH", "Enchantment"
    EVOCATION = "EVOC", "Evocation"
    ILLUSION = "ILL", "Illusion"
    NECROMANCY = "NECRO", "Necromancy"
    TRANSMUTATION = "TRANS", "Transmutation"
