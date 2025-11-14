# content/models.py
from django.db import models
from core.models import TimeStampedModel, Language

class Subtopic(TimeStampedModel):
    therapy_area = models.ForeignKey("brands.TherapyArea", on_delete=models.PROTECT, related_name="subtopics")
    slug = models.SlugField(max_length=128, unique=True)
    default_thumbnail_url = models.URLField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.slug

class SubtopicI18n(TimeStampedModel):
    subtopic = models.ForeignKey(Subtopic, on_delete=models.CASCADE, related_name="i18n")
    language = models.ForeignKey(Language, on_delete=models.PROTECT, to_field="code", db_column="language")
    name_local = models.CharField(max_length=256)
    summary_local = models.TextField(blank=True, null=True)
    thumbnail_url = models.URLField(blank=True, null=True)

    class Meta:
        unique_together = [("subtopic", "language")]

class Video(TimeStampedModel):
    subtopic = models.ForeignKey(Subtopic, on_delete=models.PROTECT, related_name="videos")
    slug = models.SlugField(max_length=128, unique=True)
    title_en = models.CharField(max_length=256, unique=True)  # unique in English
    keywords_en = models.TextField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["title_en"], name="idx_video_title_en"),
            models.Index(fields=["sort_order"], name="idx_video_sort"),
        ]

    def __str__(self):
        return self.title_en

class VideoI18n(TimeStampedModel):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="i18n")
    language = models.ForeignKey(Language, on_delete=models.PROTECT, to_field="code", db_column="language")
    title_local = models.CharField(max_length=256)
    keywords_local = models.TextField(blank=True, null=True)
    youtube_url = models.URLField()  # the video asset in this language (YouTube)
    thumbnail_url = models.URLField(blank=True, null=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        unique_together = [("video", "language")]
        indexes = [
            models.Index(fields=["title_local"], name="idx_videoi18n_title_local"),
        ]
