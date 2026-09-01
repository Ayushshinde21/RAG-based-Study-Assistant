from dotenv import load_dotenv
load_dotenv()

from utils.audio_processor import get_audio_path
from utils.transcriber import transcribe, save_transcript

# Step 1 - Get audio
audio = get_audio_path(r"C:\Users\frmxg\Downloads\English_Vertical_Sample (2).mp4")

# Step 2 - Transcribe
transcript = transcribe(audio)

# Step 3 - Save
path = save_transcript(transcript, audio)

print(f"\n📄 Transcript preview:")
print(transcript[:500])
