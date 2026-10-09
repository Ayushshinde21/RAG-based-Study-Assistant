import os
import tempfile
import subprocess
import yt_dlp
from pathlib import Path

# Folder where all audio files will be saved
AUDIO_DIR = "audio_files"
os.makedirs(AUDIO_DIR, exist_ok=True)


class YouTubeBlockedError(RuntimeError):
    """Raised when YouTube refuses the download (403 / bot check) on every strategy."""


def _get_cookie_file():
    """
    Cookies are read from a secret (never from a file committed to git).
      - Streamlit Cloud: App settings -> Secrets -> YT_COOKIES = '''<netscape cookies>'''
      - Local dev: set env var YT_COOKIES, or keep an untracked cookies.txt
    Returns a path, or None if no cookies are configured.
    """
    data = os.getenv("YT_COOKIES")
    if not data:
        try:
            import streamlit as st
            data = st.secrets.get("YT_COOKIES")
        except Exception:
            data = None

    if data:
        path = os.path.join(tempfile.gettempdir(), "yt_cookies.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(data.strip() + "\n")
        return path

    return "cookies.txt" if os.path.exists("cookies.txt") else None


def _get_proxy():
    """Optional proxy (e.g. residential) for hosts whose IPs YouTube blocks."""
    proxy = os.getenv("YT_PROXY")
    if not proxy:
        try:
            import streamlit as st
            proxy = st.secrets.get("YT_PROXY")
        except Exception:
            proxy = None
    return proxy or None


# YouTube blocks/changes individual player clients all the time, so instead of
# hard-coding one (tv_embedded was returning 403), try several in order.
_CLIENT_STRATEGIES = [None, ["tv"], ["mweb"], ["web_safari"], ["android_vr"]]


def download_youtube_audio(url: str) -> str:
    """
    Download audio from a YouTube URL.
    Returns the path to the saved .mp3 file.
    Raises YouTubeBlockedError if YouTube blocks every strategy.
    """
    output_template = os.path.join(AUDIO_DIR, "%(title)s.%(ext)s")
    cookie_file = _get_cookie_file()
    proxy = _get_proxy()
    last_error = None

    for clients in _CLIENT_STRATEGIES:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "restrictfilenames": True,
            "noplaylist": True,
            "retries": 3,
            "socket_timeout": 30,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
            "no_warnings": True,
            # Recent yt-dlp versions need a JS runtime to solve YouTube's
            # challenges (nodejs is installed via packages.txt). Ignored by
            # versions that don't know this option.
            "js_runtimes": {"node": {}},
        }
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file
        if proxy:
            ydl_opts["proxy"] = proxy
        if clients:
            ydl_opts["extractor_args"] = {"youtube": {"player_client": clients}}

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                raw_path = ydl.prepare_filename(info)
                audio_path = os.path.splitext(raw_path)[0] + ".mp3"

            if os.path.exists(audio_path):
                print(f"✅ Downloaded: {audio_path} (client: {clients or 'default'})")
                return audio_path
            last_error = FileNotFoundError(f"Expected file not found: {audio_path}")
        except yt_dlp.utils.DownloadError as e:
            last_error = e
            print(f"⚠️ yt-dlp failed with client {clients or 'default'}: {e}")

    raise YouTubeBlockedError(
        "YouTube blocked the download from this server (HTTP 403 / bot check). "
        "Please download the video yourself and use the Upload tab instead. "
        f"Details: {last_error}"
    )


def extract_audio_from_video(video_path: str) -> str:
    """
    Extract audio from an uploaded video file (.mp4, .mkv, .avi etc.)
    Returns the path to the saved .mp3 file.
    """
    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    output_path = os.path.join(AUDIO_DIR, video_path.stem + ".mp3")

    command = [
        "ffmpeg",
        "-i", str(video_path),   # input file
        "-map", "a",             # audio only
        # Whisper/Sarvam only need mono 16kHz — matches utils/transcriber.py's
        # chunking format. A smaller file extracts faster and every
        # downstream step (chunking, upload, transcription) is quicker too.
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "libmp3lame",
        "-b:a", "64k",
        output_path,
        "-y",                    # overwrite if exists
        "-loglevel", "quiet"
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    print(f"✅ Audio extracted: {output_path}")
    return output_path


def extract_audio_from_audio(audio_path: str) -> str:
    """
    If user uploads an audio file directly (.wav, .m4a etc.),
    convert it to .mp3 for consistency.
    Returns the path to the .mp3 file.
    """
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # already mp3 — just return as is
    if audio_path.suffix.lower() == ".mp3":
        return str(audio_path)

    output_path = os.path.join(AUDIO_DIR, audio_path.stem + ".mp3")

    command = [
        "ffmpeg",
        "-i", str(audio_path),
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "libmp3lame",
        "-b:a", "64k",
        output_path,
        "-y",
        "-loglevel", "quiet"
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    print(f"✅ Converted to mp3: {output_path}")
    return output_path


def get_audio_path(source: str) -> str:
    """
    Main entry point.
    Figures out what the source is and returns a clean .mp3 path.

    source can be:
      - a YouTube URL
      - a path to a video file
      - a path to an audio file
    """
    if source.startswith("http://") or source.startswith("https://"):
        return download_youtube_audio(source)

    path = Path(source)
    video_formats = [".mp4", ".mkv", ".avi", ".mov", ".webm"]
    audio_formats = [".mp3", ".wav", ".m4a", ".ogg", ".flac"]

    if path.suffix.lower() in video_formats:
        return extract_audio_from_video(source)
    elif path.suffix.lower() in audio_formats:
        return extract_audio_from_audio(source)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")