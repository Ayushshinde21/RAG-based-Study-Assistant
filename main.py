from dotenv import load_dotenv
load_dotenv()

print("✅ Study Assistant - Environment loaded")
from utils.audio_processor import get_audio_path

# Test with a short YouTube video
audio = get_audio_path("https://www.youtube.com/watch?v=xlYJhtL0qbQ")
print(f"Audio saved at: {audio}")
