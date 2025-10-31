import os, openai, random
from moviepy.editor import *
from pydub import AudioSegment
import subprocess

openai.api_key = os.getenv("OPENAI_API_KEY")

RAW_PATH = "raw_clips"
OUT_PATH = "output_clips"

def transcribe_audio(video_path):
    audio_path = "temp_audio.mp3"
    subprocess.call(['ffmpeg', '-i', video_path, '-vn', '-acodec', 'mp3', audio_path, '-y'])
    with open(audio_path, "rb") as f:
        transcript = openai.Audio.transcriptions.create(model="whisper-1", file=f)
    return transcript.text

def generate_overlay_text(transcript):
    prompt = f"Write a catchy short caption for a viral English IRL clip. Text should match the moment tone and be engaging:\n\n{transcript}"
    res = openai.Chat.completions.create(model="gpt-4-turbo", messages=[{"role": "user", "content": prompt}])
    return res.choices[0].message.content.strip()

def edit_clip(video_path):
    print(f"Processing: {video_path}")
    transcript = transcribe_audio(video_path)
    overlay_text = generate_overlay_text(transcript)

    clip = VideoFileClip(video_path).subclip(0, min(clip.duration, 25))
    blurred_bg = clip.resize(height=1080).fx(vfx.blur, 10)
    main = clip.resize(height=1080).margin(10)
    final = CompositeVideoClip([
        blurred_bg,
        main.set_position("center"),
        TextClip(overlay_text, fontsize=70, color='white', font='Arial-Bold', size=(1080, None), method='caption')
        .set_position(("center", 50)).set_duration(clip.duration)
    ])
    out_file = os.path.join(OUT_PATH, os.path.basename(video_path))
    final.write_videofile(out_file, codec="libx264", audio_codec="aac")
    print(f"Saved → {out_file}")

for file in os.listdir(RAW_PATH):
    if file.endswith((".mp4", ".mov")):
        edit_clip(os.path.join(RAW_PATH, file))
