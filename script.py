from moviepy.editor import VideoFileClip, CompositeVideoClip, vfx, AudioFileClip
from pydub import AudioSegment
import os, random, numpy as np

raw_folder = "raw_clips"
sound_folder = "soundVFX"
output_folder = "output_clips"

# Load all raw clips
clips = [os.path.join(raw_folder, f) for f in os.listdir(raw_folder) if f.endswith(".mp4")]

for i, path in enumerate(clips):
    clip = VideoFileClip(path)

    # Convert horizontal → vertical
    bg = clip.resize(height=1920).fx(vfx.blur, 50)
    fg = clip.resize(height=1080).set_position('center')
    video = CompositeVideoClip([bg, fg])

    # 🔊 Analyze sound for peaks (moments)
    audio_path = "temp_audio.wav"
    clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
    audio = AudioSegment.from_wav(audio_path)
    samples = np.array(audio.get_array_of_samples())
    samples = samples.astype(np.float32)
    samples = np.abs(samples)
    threshold = np.percentile(samples, 97)  # top 3% loudest
    peaks = np.where(samples > threshold)[0]

    # If peaks exist → add whoosh & mini zoom
    if len(peaks) > 0:
        peak_time = (peaks[0] / audio.frame_rate)
        end_time = min(peak_time + 0.5, clip.duration)
        focus = video.subclip(peak_time, end_time).fx(vfx.zoom_in, 1.1)
        video = CompositeVideoClip([video.set_start(0), focus.set_start(peak_time)])

        # Add whoosh sound
        sfx_list = [os.path.join(sound_folder, f) for f in os.listdir(sound_folder) if f.endswith(".mp3")]
        if sfx_list:
            sfx = AudioFileClip(random.choice(sfx_list)).volumex(0.5)
            sfx = sfx.set_start(peak_time)
            video = CompositeVideoClip([video, sfx.set_duration(0.5)])

    # Add smooth fade at start and end
    video = video.fadein(0.4).fadeout(0.4)

    # Export
    output_path = os.path.join(output_folder, f"moment_clip_{i+1}.mp4")
    video.write_videofile(output_path, fps=30)

    # Cleanup
    os.remove(audio_path)

print("✅ All moment clips processed and effects added!")
