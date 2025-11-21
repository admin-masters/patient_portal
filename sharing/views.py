# sharing/views.py
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import ShareLink, LinkVisit

class ShareLinkView(TemplateView):
    template_name = "sharing/placeholder.html"

    def dispatch(self, request, *args, **kwargs):
        self.link = get_object_or_404(ShareLink, token=kwargs.get("token"))
        # Log visit
        LinkVisit.objects.create(
            share_link=self.link,
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            referer=request.META.get("HTTP_REFERER", ""),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["link"] = self.link
        return ctx
