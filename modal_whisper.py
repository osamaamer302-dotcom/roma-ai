
import modal
import tempfile
import os

app = modal.App("roma-ai-whisper")

image = (
    modal.Image.debian_slim()
    .pip_install("openai-whisper", "ffmpeg-python")
    .apt_install("ffmpeg")
)

@app.function(image=image, gpu="any", timeout=300)
def transcribe(video_bytes: bytes, task: str = "transcribe"):
    import whisper, tempfile
    model = whisper.load_model("base")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
        f.write(video_bytes)
        tmp_path = f.name
    result = model.transcribe(tmp_path, task=task)
    os.remove(tmp_path)
    return result

@app.function(image=image, gpu="any", timeout=300)
def remove_silence(video_bytes: bytes, threshold: float = 0.5):
    import whisper, tempfile, subprocess
    model = whisper.load_model("base")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
        f.write(video_bytes)
        input_path = f.name
    output_path = input_path.replace(".mp4", "_out.mp4")
    result = model.transcribe(input_path, word_timestamps=True)
    segments = result.get("segments", [])
    if not segments:
        return None
    padding = 0.1
    merged = []
    for seg in segments:
        start = max(0, seg["start"] - padding)
        end = seg["end"] + padding
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    vf = "+".join([f"between(t,{s},{e})" for s, e in merged])
    fc = f"[0:v]select='{vf}',setpts=N/FRAME_RATE/TB[v];[0:a]aselect='{vf}',asetpts=N/SR/TB[a]"
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", output_path],
        check=True,
        capture_output=True
    )
    os.remove(input_path)
    with open(output_path, "rb") as f:
        return f.read()

@app.function(image=image, gpu="any", timeout=300)
def burn_captions(video_bytes: bytes, srt_content: str, font_size: int = 24, color: str = "FFFFFF"):
    import tempfile, subprocess, os

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
        f.write(video_bytes)
        input_path = f.name

    srt_path = input_path.replace(".mp4", ".srt")
    output_path = input_path.replace(".mp4", "_captioned.mp4")

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"subtitles={srt_path}:force_style='FontSize={font_size},PrimaryColour=&H{color}&,Outline=2,Shadow=1'",
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    os.remove(input_path)
    os.remove(srt_path)

    with open(output_path, "rb") as f:
        return f.read()
