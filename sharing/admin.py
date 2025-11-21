# sharing/admin.py
from django.contrib import admin
from .models import ShareLink, ShareEvent, LinkVisit

admin.site.register(ShareLink)
admin.site.register(ShareEvent)
admin.site.register(LinkVisit)
