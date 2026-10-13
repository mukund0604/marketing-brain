"""Assemble the demo video from the Playwright capture, beat timestamps, TTS voiceover and title cards.
Waits are sped up 8x with a visible badge; each beat's footage is fit to its voiceover; captions burned in."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
CAP = ROOT / "capture"
VO = ROOT / "vo"
TMP = ROOT / "build"
TMP.mkdir(exist_ok=True)
FPS = 30
WAIT_SPEED = 8.0
FONT = "/System/Library/Fonts/Helvetica.ttc"

beats = json.loads((CAP / "beats.json").read_text())
durs = json.loads((VO / "durations.json").read_text())
lines = json.loads((VO / "lines.json").read_text())


def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-2000:])


def probe(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True).stdout.strip())


# beat windows and wait windows from the capture log
bt = {b["name"]: b["t"] for b in beats if b["kind"] == "beat"}
waits = {}
for b in beats:
    if b["kind"] == "wait":
        name, edge = b["name"].rsplit("-", 1)
        waits.setdefault(name, {})[edge] = b["t"]
order = ["problem", "brain", "explore", "ask", "compare", "learn"]
bounds = {name: (bt[name], bt[order[i + 1]] if i + 1 < len(order) else bt["end"] + 1.5) for i, name in enumerate(order)}


def pieces(start, end):
    """Split a beat window into (a, b, is_wait) pieces."""
    ws = sorted((w["start"], w["end"]) for w in waits.values() if start <= w.get("start", -1) < end and "end" in w)
    out, cur = [], start
    for a, b in ws:
        if a > cur:
            out.append((cur, a, False))
        out.append((a, b, True))
        cur = b
    if cur < end:
        out.append((cur, end, False))
    return out


def beat_clip(name, reserve=0.0):
    start, end = bounds[name]
    ps = pieces(start, end)
    target = durs[name] + 0.8 - reserve
    live = sum(b - a for a, b, w in ps if not w)
    sped = sum((b - a) / WAIT_SPEED for a, b, w in ps if w)
    factor = max(.5, min(1.6, live / max(target - sped, 0.1)))  # >1 speeds up, <1 slows down
    parts = []
    for i, (a, b, w) in enumerate(ps):
        out = TMP / f"{name}_{i}.mp4"
        sp = WAIT_SPEED if w else factor
        vf = f"trim={a}:{b},setpts=(PTS-STARTPTS)/{sp},fps={FPS},crop=1536:864:0:0,scale=1920:1080:flags=lanczos"
        if w:
            vf += (f",drawbox=x=1696:y=36:w=188:h=64:color=0x0A0B0F@0.88:t=fill,"
                   f"drawtext=fontfile={FONT}:text='{int(WAIT_SPEED)}x speed':x=1716:y=54:fontsize=28:fontcolor=white")
        run(["ffmpeg", "-y", "-i", str(CAP / "raw.webm"), "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out)])
        parts.append(out)
    lst = TMP / f"{name}.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    joined = TMP / f"{name}_v.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])
    return joined


def card_clip(png, seconds, name):
    out = TMP / f"{name}_v.mp4"
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(png), "-t", str(seconds), "-vf", f"fps={FPS},scale=1920:1080,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out)])
    return out


def with_audio(video, audio, name, lead=0.3, min_len=0):
    """Pad video (freeze last frame) to fit the voiceover; mux audio delayed by `lead` seconds."""
    vd, ad = probe(video), (probe(audio) if audio else 0)
    total = max(vd, ad + lead + 0.5, min_len)
    out = TMP / f"{name}_av.mp4"
    afilter = (f"[1:a]adelay={int(lead * 1000)}|{int(lead * 1000)},apad,atrim=0:{total},aresample=48000[a]" if audio
               else f"anullsrc=r=48000:cl=stereo,atrim=0:{total}[a]")
    inputs = ["-i", str(video)] + (["-i", str(audio)] if audio else [])
    run(["ffmpeg", "-y", *inputs, "-filter_complex", f"[0:v]tpad=stop_mode=clone:stop_duration={max(0, total - vd)}[v];{afilter}",
         "-map", "[v]", "-map", "[a]", "-t", str(total), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k", "-ac", "2", str(out)])
    return out, total


def ass_time(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


if __name__ == "__main__":
    segs, cues, t = [], [], 0.0
    # intro card carries the opening of the "problem" voiceover; the Ask empty state carries the rest
    intro = card_clip(ROOT / "intro.png", 4.5, "intro")
    prob_v = beat_clip("problem")
    cat = TMP / "problem_full.txt"
    cat.write_text(f"file '{intro.name}'\nfile '{prob_v.name}'\n")
    pv = TMP / "problem_full_v.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(cat), "-c", "copy", str(pv)])
    STILLS = {"compare": "compare_sbs.png", "learn": "learn_sbs.png"}  # full-screen control vs brain, 5s each
    plan = [("problem", pv)]
    for n in order[1:]:
        if n in STILLS:
            v = beat_clip(n, reserve=4.0)
            still = card_clip(ROOT / STILLS[n], 5.0, f"{n}_still")
            lst2 = TMP / f"{n}_withstill.txt"
            lst2.write_text(f"file '{v.name}'\nfile '{still.name}'\n")
            v2 = TMP / f"{n}_withstill_v.mp4"
            run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst2), "-c", "copy", str(v2)])
            plan.append((n, v2))
        else:
            plan.append((n, beat_clip(n)))
    for name, v in plan:
        av, total = with_audio(v, VO / f"{name}.wav", name, lead=0.6 if name == "problem" else 0.3)
        segs.append(av)
        cues.append((t + (0.6 if name == "problem" else 0.3), durs[name], lines[name]))
        t += total
    outro = card_clip(ROOT / "outro.png", 1, "outro")
    av, total = with_audio(outro, VO / "outro.wav", "outro", lead=0.5, min_len=durs["outro"] + 2)
    segs.append(av)
    cues.append((t + 0.5, durs["outro"], lines["outro"]))
    t += total

    # captions: split each voiceover line into short sentences, timed by length
    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "",
           "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: Cap,Helvetica Neue,40,&H00FFFFFF,&H00FFFFFF,&H000B0A0A,&H330B0A0A,0,0,0,0,100,100,0,0,3,14,0,2,260,260,54,1", "",
           "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for start, dur, text in cues:
        phrases = [c.strip() for c in re.split(r"(?<=[.:!?,])\s+", text) if c.strip()]
        merged, buf = [], ""
        for ph in phrases:  # greedy: captions of at most ~62 characters
            if buf and len(buf) + 1 + len(ph) > 62:
                merged.append(buf); buf = ph
            else:
                buf = f"{buf} {ph}".strip()
        if buf:
            merged.append(buf)
        total_chars = sum(len(m) for m in merged)
        cur = start
        for m in merged:
            d = dur * len(m) / total_chars
            ass.append(f"Dialogue: 0,{ass_time(cur)},{ass_time(cur + d)},Cap,,0,0,0,,{m}")
            cur += d
    (TMP / "captions.ass").write_text("\n".join(ass))

    lst = TMP / "all.txt"
    lst.write_text("".join(f"file '{s.name}'\n" for s in segs))
    joined = TMP / "joined.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])
    final = ROOT / "marketing-brain-demo.mp4"
    run(["ffmpeg", "-y", "-i", str(joined), "-vf", f"subtitles={TMP / 'captions.ass'}", "-c:v", "libx264", "-preset", "medium",
         "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(final)])
    print("final", final, round(probe(final), 1), "s")
