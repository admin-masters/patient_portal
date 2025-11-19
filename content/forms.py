# content/forms.py
from django import forms
from django.core.files.storage import default_storage
import uuid, pathlib

from .models import Subtopic, SubtopicI18n, VideoI18n
from .validators import validate_youtube_url

def _save_thumb(file_obj, prefix: str, obj_id: int) -> str:
    ext = pathlib.Path(file_obj.name).suffix or ".jpg"
    key = f"{prefix}/{obj_id}/{uuid.uuid4().hex}{ext}"
    saved_path = default_storage.save(key, file_obj)
    return default_storage.url(saved_path)  # -> "/media/..." in dev

class SubtopicAdminForm(forms.ModelForm):
    upload_thumbnail = forms.FileField(required=False, help_text="Upload image; sets default thumbnail URL.")

    class Meta:
        model = Subtopic
        fields = ["therapy_area", "slug", "default_thumbnail_url", "upload_thumbnail", "sort_order", "is_active"]

    def save(self, commit=True):
        obj = super().save(commit=False)
        file_obj = self.cleaned_data.get("upload_thumbnail")
        if file_obj:
            obj.default_thumbnail_url = _save_thumb(file_obj, "content/subtopics", obj.pk or 0)
        if commit:
            obj.save()
        return obj

class SubtopicI18nAdminForm(forms.ModelForm):
    upload_thumbnail = forms.FileField(required=False, help_text="Upload image; sets localized thumbnail URL.")

    class Meta:
        model = SubtopicI18n
        fields = ["subtopic", "language", "name_local", "summary_local", "thumbnail_url", "upload_thumbnail"]

    def save(self, commit=True):
        obj = super().save(commit=False)
        file_obj = self.cleaned_data.get("upload_thumbnail")
        if file_obj:
            obj.thumbnail_url = _save_thumb(file_obj, "content/subtopics", obj.subtopic_id or 0)
        if commit:
            obj.save()
        return obj

class VideoI18nAdminForm(forms.ModelForm):
    upload_thumbnail = forms.FileField(required=False, help_text="Upload image; sets video thumbnail URL.")

    class Meta:
        model = VideoI18n
        fields = ["video", "language", "title_local", "keywords_local", "youtube_url", "thumbnail_url", "upload_thumbnail", "is_published"]

    def clean_youtube_url(self):
        return validate_youtube_url(self.cleaned_data["youtube_url"])

    def save(self, commit=True):
        obj = super().save(commit=False)
        file_obj = self.cleaned_data.get("upload_thumbnail")
        if file_obj:
            obj.thumbnail_url = _save_thumb(file_obj, "content/videos", obj.video_id or 0)
        if commit:
            obj.save()
        return obj
