"""Helper functions of the quiz app."""

import re
from urllib.parse import parse_qs, urlparse

# Hostnames that are accepted as YouTube URLs.
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}

# Path prefixes of video URLs like ``/shorts/<id>``.
VIDEO_PATH_PREFIXES = ("shorts", "embed", "live", "v")

VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


def normalize_youtube_url(url: str):
    """Return the standard URL of a YouTube video.

    Short links (``youtu.be``), mobile links, links with additional
    parameters and ``shorts``, ``embed`` or ``live`` links all become
    ``https://www.youtube.com/watch?v=<id>``. The client embeds the video
    with this URL, which only works for the standard format.

    Args:
        url: A URL that may point to a YouTube video.

    Returns:
        The standard URL, or ``None`` if the URL is not a YouTube video URL.
    """
    video_id = extract_video_id(url)

    if video_id is None:
        return None

    return f"https://www.youtube.com/watch?v={video_id}"


def extract_video_id(url: str):
    """Return the video id of a YouTube URL, or ``None`` if there is none."""
    parsed = urlparse(url)

    if parsed.hostname not in YOUTUBE_HOSTS:
        return None

    if parsed.hostname == "youtu.be":
        candidate = parsed.path.strip("/")
    else:
        candidate = _get_id_candidate(parsed)

    return candidate if VIDEO_ID_PATTERN.match(candidate) else None


def _get_id_candidate(parsed_url) -> str:
    """Read the possible video id from a ``youtube.com`` URL."""
    if parsed_url.path == "/watch":
        return parse_qs(parsed_url.query).get("v", [""])[0]

    parts = parsed_url.path.strip("/").split("/")

    if len(parts) == 2 and parts[0] in VIDEO_PATH_PREFIXES:
        return parts[1]

    return ""
