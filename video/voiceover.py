"""Generate the demo voiceover with Gemini TTS, one clip per beat -> video/vo/<beat>.wav + vo/durations.json"""
import json
import os
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

ROOT = Path(__file__).parent
load_dotenv(ROOT.parent / ".env")
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
OUT = ROOT / "vo"
OUT.mkdir(exist_ok=True)

LINES = {
    "problem": "Every brand's marketing knowledge is scattered. Brand books in PDFs, ad results in a warehouse, reviews on Amazon and Reddit, and client feedback buried in approval threads. So AI creative tools forget everything, and repeat the same mistakes.",
    "brain": "Marketing Brain puts all of it into one memory, on HydraDB. Five layers: a brand book down to hex codes and FDA rules, eighteen months of campaigns with daily ad performance, what consumers say across seven platforms, the market, and the client's own feedback. All loaded in our production brand-graph schema, with HydraDB's Bring Your Own Graph.",
    "explore": "And it's browsable. Every node is something the brain knows, ringed by how it performed. Open a campaign, and you get the intelligence: it missed its target, here's why, and here are the creatives that underperformed.",
    "ask": "Ask a question, and the agent decides which layers to search. Then it shows its work: every HydraDB query, every result ranked by relevance, which memories it actually used, and the graph paths it followed. The summer SPF campaign missed because of white-cast complaints, and you can see exactly which reviews prove it.",
    "compare": "Now, the same ad request, with and without memory. Without it, you get banned words, invented packaging, and no legal copy. With the brain: the real logo and packshot, deeper skin tones because that's what won before, and the exact FDA wording legal requires. Every decision traces back to a memory.",
    "learn": "And when the client pushes back, the brain remembers. Legal's new rule is written to HydraDB memory, and on the very next generation, it's retrieved, tagged new, and applied.",
    "outro": "Marketing Brain. A three-sixty memory on HydraDB that every creative agent reads from, shows its work, and learns from every rejection.",
}


def tts(item):
    name, text = item
    r = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=f"Read this as a confident, warm, unhurried product-demo narrator: {text}",
        config=types.GenerateContentConfig(response_modalities=["AUDIO"], speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")))))
    pcm = r.candidates[0].content.parts[0].inline_data.data
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
    return name, round(len(pcm) / 2 / 24000, 2)


if __name__ == "__main__":
    with ThreadPoolExecutor(7) as ex:
        durs = dict(ex.map(tts, LINES.items()))
    (OUT / "durations.json").write_text(json.dumps(durs, indent=1))
    (OUT / "lines.json").write_text(json.dumps(LINES, indent=1))
    print(durs, "total", round(sum(durs.values()), 1))
