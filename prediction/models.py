from django.db import models

VALID_SPECIES = [
    ('Bream', 'Bream'),
    ('Parkki', 'Parkki'),
    ('Perch', 'Perch'),
    ('Pike', 'Pike'),
    ('Roach', 'Roach'),
    ('Smelt', 'Smelt'),
    ('Whitefish', 'Whitefish'),
]

class FishData(models.Model):
    species = models.CharField(max_length=20, choices=VALID_SPECIES)
    length1 = models.FloatField()
    length2 = models.FloatField()
    length3 = models.FloatField()
    height = models.FloatField()
    width = models.FloatField()
    predicted_weight = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.species} (ID: {self.id})"