# content/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Subtopic, SubtopicI18n, Video, VideoI18n
from .forms import SubtopicAdminForm, SubtopicI18nAdminForm, VideoI18nAdminForm

class SubtopicI18nInline(admin.TabularInline):
    model = SubtopicI18n
    form = SubtopicI18nAdminForm
    extra = 0
    fields = ("language", "name_local", "thumbnail_url", "upload_thumbnail", "summary_local")
    show_change_link = True

class VideoInline(admin.TabularInline):
    model = Video
    extra = 0
    fields = ("slug", "title_en", "sort_order", "is_active")
    show_change_link = True

class VideoI18nInline(admin.TabularInline):
    model = VideoI18n
    form = VideoI18nAdminForm
    extra = 0
    fields = ("language", "title_local", "youtube_url", "thumbnail_url", "upload_thumbnail", "is_published")
    show_change_link = True

@admin.register(Subtopic)
class SubtopicAdmin(admin.ModelAdmin):
    form = SubtopicAdminForm
    list_display = ("slug", "therapy_area", "sort_order", "is_active", "thumb")
    list_filter = ("therapy_area", "is_active")
    search_fields = ("slug",)
    inlines = [SubtopicI18nInline, VideoInline]
    ordering = ("therapy_area__name", "sort_order", "slug")

    def thumb(self, obj):
        if obj.default_thumbnail_url:
            return format_html('<img src="{}" style="height:32px;border-radius:4px;border:1px solid #ddd;">', obj.default_thumbnail_url)
        return "-"
    thumb.short_description = "Thumbnail"

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title_en", "subtopic", "sort_order", "is_active")
    list_filter = ("subtopic__therapy_area", "subtopic")
    search_fields = ("title_en", "keywords_en")
    inlines = [VideoI18nInline]
    ordering = ("subtopic__therapy_area__name", "subtopic__slug", "sort_order", "title_en")

@admin.register(SubtopicI18n)
class SubtopicI18nAdmin(admin.ModelAdmin):
    form = SubtopicI18nAdminForm
    list_display = ("subtopic", "language", "name_local", "thumb")
    list_filter = ("language__code", "subtopic__therapy_area")
    search_fields = ("name_local",)
    ordering = ("subtopic__therapy_area__name", "subtopic__slug", "language__code")

    def thumb(self, obj):
        if obj.thumbnail_url:
            return format_html('<img src="{}" style="height:32px;border-radius:4px;border:1px solid #ddd;">', obj.thumbnail_url)
        return "-"
    thumb.short_description = "Thumbnail"

@admin.register(VideoI18n)
class VideoI18nAdmin(admin.ModelAdmin):
    form = VideoI18nAdminForm
    list_display = ("video", "language", "title_local", "is_published", "open_youtube")
    list_filter = ("language__code", "is_published", "video__subtopic__therapy_area")
    search_fields = ("title_local", "keywords_local", "youtube_url")
    ordering = ("video__subtopic__therapy_area__name", "video__subtopic__slug", "video__sort_order", "language__code")

    def open_youtube(self, obj):
        return format_html('<a href="{}" target="_blank">open</a>', obj.youtube_url)
    open_youtube.short_description = "YouTube"
