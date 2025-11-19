# content/validators.py
from urllib.parse import urlparse, parse_qs
from django.core.exceptions import ValidationError

ALLOWED_HOSTS = {
    "youtube.com", "www.youtube.com", "m.youtube.com",
    "youtu.be", "www.youtu.be",
}

def _extract_youtube_id(url: str) -> str | None:
    p = urlparse(url)
    host = (p.netloc or "").lower()
    if host not in ALLOWED_HOSTS:
        return None

    # youtu.be/<id>
    if "youtu.be" in host:
        vid = p.path.strip("/").split("/")[0]
        return vid or None

    # youtube.com/watch?v=ID
    if p.path == "/watch":
        return parse_qs(p.query).get("v", [None])[0]

    # youtube.com/embed/ID or /shorts/ID
    parts = [seg for seg in p.path.strip("/").split("/") if seg]
    if len(parts) >= 2 and parts[0] in {"embed", "shorts"}:
        return parts[1]

    return None

def validate_youtube_url(value: str):
    vid = _extract_youtube_id(value)
    if not vid or len(vid) < 8:
        raise ValidationError("Enter a valid YouTube URL (watch?v=, youtu.be/, /embed/, or /shorts/).")
    return value
