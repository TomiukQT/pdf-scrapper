from django.contrib import admin
from .models import Resolution, Representative, ExtendedResolution

admin.site.register(Resolution)
admin.site.register(ExtendedResolution)
admin.site.register(Representative)
