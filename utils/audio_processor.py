import os
import subprocess
import yt_dlp
from pathlib import Path

# Folder where all audio files will be saved
AUDIO_DIR = "audio_files"
os.makedirs(AUDIO_DIR, exist_ok=True)


def download_youtube_audio(url: str) -> str:
    """
    Download audio from a YouTube URL.
    Returns the path to the saved .mp3 file.
    """
    output_template = os.path.join(AUDIO_DIR, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "cookiefile": "cookies.txt",
        "extractor_args": {
            "youtube": {
                "player_client": ["tv_embedded"],  # ← change to this
            }
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "audio")
        # clean title for filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        audio_path = os.path.join(AUDIO_DIR, f"{safe_title}.mp3")

    print(f"✅ Downloaded: {audio_path}")
    return audio_path


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
        "-q:a", "0",             # best quality
        "-map", "a",             # audio only
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
    
