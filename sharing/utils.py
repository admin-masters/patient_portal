# sharing/utils.py
from urllib.parse import urlparse, parse_qs
from typing import Optional
from content.models import Video, VideoI18n, Subtopic, SubtopicI18n

# --- Tiny i18n for UI labels (can expand later) ---
_UI = {
    "for_more_videos": {
        "en": "For more videos click here",
        "hi": "अधिक वीडियो के लिए यहाँ क्लिक करें",
        "te": "ఇంకా వీడియోల కోసం ఇక్కడ నొక్కండి",
        "ml": "കൂടുതൽ വീഡിയോകൾക്കായി ഇവിടെ ക്ലിക്ക് ചെയ്യുക",
        "mr": "अधिक व्हिडिओंसाठी येथे क्लिक करा",
        "kn": "ಹೆಚ್ಚು ವೀಡಿಯೋಗಳಿಗೆ ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ",
        "ta": "மேலும் வீடியோக்களுக்கு இங்கே சொடுக்கவும்",
        "bn": "আরও ভিডিওর জন্য এখানে ক্লিক করুন",
    },
    "back_to_home": {
        "en": "Back to home",
        "hi": "होम पर वापस जाएँ",
        "te": "హోమ్‌కు తిరిగి వెళ్లు",
        "ml": "ഹോം പേജിലേക്ക് മടങ്ങുക",
        "mr": "मुख्यपृष्ठावर परत जा",
        "kn": "ಮುಖಪುಟಕ್ಕೆ ಹಿಂತಿರುಗಿ",
        "ta": "முகப்பிற்கு திரும்பவும்",
        "bn": "হোমে ফিরে যান",
    },
    "subtopics": {
        "en": "Subtopics",
        "hi": "उप-विषय",
        "te": "ఉప-విషయాలు",
        "ml": "ഉപവിഷയങ്ങൾ",
        "mr": "उपविषय",
        "kn": "ಉಪವಿಷಯಗಳು",
        "ta": "துணைத் தலைப்புகள்",
        "bn": "উপ-বিষয়",
    },
}

def ui_label(key: str, lang: str) -> str:
    return _UI.get(key, {}).get(lang, _UI.get(key, {}).get("en", key))

# --- YouTube id extraction (from validator logic) ---
def youtube_id(url: str) -> Optional[str]:
    try:
        p = urlparse(url)
    except Exception:
        return None
    host = (p.netloc or "").lower()
    if "youtu.be" in host:
        vid = p.path.strip("/").split("/")[0]
        return vid or None
    if "youtube.com" in host:
        if p.path == "/watch":
            return parse_qs(p.query).get("v", [None])[0]
        parts = [seg for seg in p.path.strip("/").split("/") if seg]
        if len(parts) >= 2 and parts[0] in {"embed", "shorts"}:
            return parts[1]
    return None

# --- Localization helpers & fallbacks ---
def title_for_video(video: Video, lang: str) -> str:
    vloc = VideoI18n.objects.filter(video=video, language_id=lang).first()
    return vloc.title_local if vloc else video.title_en

def name_for_subtopic(subtopic: Subtopic, lang: str) -> str:
    sloc = SubtopicI18n.objects.filter(subtopic=subtopic, language_id=lang).first()
    return sloc.name_local if sloc else subtopic.slug

def thumb_for_video(video: Video, lang: str) -> Optional[str]:
    vloc = VideoI18n.objects.filter(video=video, language_id=lang).first()
    if vloc and vloc.thumbnail_url:
        return vloc.thumbnail_url
    v_en = VideoI18n.objects.filter(video=video, language_id="en").first()
    if v_en and v_en.thumbnail_url:
        return v_en.thumbnail_url
    # fallback to subtopic default
    return video.subtopic.default_thumbnail_url or None

def thumb_for_subtopic(subtopic: Subtopic, lang: str) -> Optional[str]:
    sloc = SubtopicI18n.objects.filter(subtopic=subtopic, language_id=lang).first()
    if sloc and sloc.thumbnail_url:
        return sloc.thumbnail_url
    return subtopic.default_thumbnail_url or None
