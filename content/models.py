# content/models.py
from django.db import models
from core.models import TimeStampedModel, Language
# REMOVE this line:
# from django.contrib.mysql.indexes import FullTextIndex

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
    title_en = models.CharField(max_length=256, unique=True)
    keywords_en = models.TextField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        # We'll add FULLTEXT via a migration (below)
        indexes = []  # optional: leave empty

    def __str__(self):
        return self.title_en

class VideoI18n(TimeStampedModel):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="i18n")
    language = models.ForeignKey(Language, on_delete=models.PROTECT, to_field="code", db_column="language")
    title_local = models.CharField(max_length=256)
    keywords_local = models.TextField(blank=True, null=True)
    youtube_url = models.URLField()
    thumbnail_url = models.URLField(blank=True, null=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        # We'll add FULLTEXT via a migration (below)
        indexes = []
