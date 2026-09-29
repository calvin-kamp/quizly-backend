import os
import tempfile

import yt_dlp


def download_audio(url: str) -> str:
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
