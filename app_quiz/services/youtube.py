"""Download of the audio of a YouTube video."""

import os
import tempfile

import yt_dlp


def download_audio(url: str) -> str:
    """Download the best available audio of a video into a temporary folder.

    Args:
        url: URL of the YouTube video. Playlists are ignored.

    Returns:
        Path of the audio file. The caller has to delete its parent folder.

    Raises:
        yt_dlp.utils.DownloadError: If the video cannot be downloaded.
    """
    tmp_dir = tempfile.mkdtemp()
    tmp_filename = os.path.join(tmp_dir, "audio.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": tmp_filename,
        "quiet": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)
