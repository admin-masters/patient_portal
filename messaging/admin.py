# messaging/admin.py
from django.contrib import admin
from .models import MessageTemplate, MessageTemplateI18n, OutboundMessage

admin.site.register(MessageTemplate)
admin.site.register(MessageTemplateI18n)
admin.site.register(OutboundMessage)
