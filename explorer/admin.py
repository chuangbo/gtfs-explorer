from django.contrib.gis import admin
from models import Stop

admin.site.register(Stop, admin.GeoModelAdmin)
