from django.contrib.gis.db import models


class Stop(models.Model):
    """A bus `stop`."""
    objects = models.GeoManager()

    code = models.CharField(max_length=5)
    name = models.CharField(max_length=100)
    point = models.PointField()

    def __unicode__(self):
        return self.code


class Route(models.Model):
    """A `route`."""
    objects = models.GeoManager()

    short_name = models.CharField(max_length=10)
    long_name = models.CharField(max_length=100)
    color = models.CharField(max_length=6)
    text_color = models.CharField(max_length=6)
    points = models.LineStringField()
    stops = models.ManyToManyField(Stop, related_name='routes')

    def __unicode__(self):
        return self.short_name
