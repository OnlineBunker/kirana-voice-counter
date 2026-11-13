import json, subprocess, os
from PIL import Image, ImageDraw, ImageFont
import requests
K = open('/tmp/gnani_key.txt').read().strip()
W, H = 1100, 760
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
if not os.path.exists(B):
    import glob
    B = glob.glob("/usr/share/fonts/truetype/**/*Bold.ttf", recursive=True)[0]; R = B
def card(path, title, lines):
    im = Image.new("RGB", (W, H), "#fbf6ee"); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 14, H], fill="#d9480f")
    d.text((70, 90), title, font=ImageFont.truetype(B, 46), fill="#1d1a16")
    y = 190
    for ln in lines:
        d.text((70, y), ln, font=ImageFont.truetype(R, 28), fill="#3a342c"); y += 52
    im.save(path)
def tts(text, path):
    r = requests.post("https://api.vachana.ai/api/v1/tts/inference", headers={"X-API-Key-ID": K},
        json={"text": text, "voice": "Nalini", "model": "timbre-v2.5", "language": "en-IN", "speed": 1.0,
              "audio_config": {"sample_rate": 24000, "container": "wav"}}, timeout=90)
    r.raise_for_status(); open(path, "wb").write(r.content)
def dur(p):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]).decode())
segs = [
 ("Kirana Voice Counter", ["A voice billing helper for small Indian shops.", "", "Built on Gnani AI Prisma v3.0 (speech to text)", "and Timbre v2.5 (text to speech).", "", "Solo entry: Yash Dhankhar, Rishihood University"],
  "Hello. This is Kirana Voice Counter, my entry for the Great Indian A I Internship Challenge. It is a voice billing helper for small shops, built on Gnani Prisma for speech to text and Gnani Timbre for text to speech."),
 ("The problem", ["A busy shopkeeper speaks orders in Hinglish.", "Typing items into a billing app is slow.", "", "Idea: say the order, get an itemised bill,", "hear it read back to confirm."],
  "A kirana shopkeeper takes orders in Hindi and Hinglish while serving other customers. Typing each item into a billing app is slow. The idea is simple. Say the order, get an itemised bill, and hear it read back so the customer can confirm."),
 ("Demo note", ["The next clip is a real run of the app in Chrome.", "The microphone input is a synthetic Hinglish order", "generated with Timbre, not a human voice.", "", "Everything after the microphone is the real pipeline:", "Prisma, parser, bill, Timbre read-back."],
  "In the next clip you will see a real run of the app. The microphone input is a synthetic Hinglish order that I generated with Timbre, so it is not a human voice. Everything after the microphone is the real pipeline."),
]
tail = [
 ("What the parser understands", ["do kilo chawal  =  2 kg rice", "dedh kilo cheeni  =  1.5 kg sugar", "ek dozen ande  =  12 eggs", "500 gram namak  =  0.5 kg salt", "atta 5 kilo  =  5 kg flour", "Words it does not know are listed, not guessed."],
  "The parser understands Hindi and Hinglish number words like ek, do, teen, dedh and dhai, and units like kilo, gram, litre, packet and dozen. Two kilo chawal becomes two kilograms of rice. Five hundred gram namak becomes half a kilo of salt. If the shopkeeper says an item that is not in the catalogue, the app lists it as not found instead of guessing, so nothing is silently billed wrong."),
 ("How it works", ["1. Browser records the order.   2. ffmpeg makes 16 kHz WAV.", "3. Prisma v3.0 returns the Hindi transcript.", "4. A rule based parser reads quantities and items,", "    for example 'do kilo chawal' = 2 kg rice.", "5. Bill from a small sample catalogue of 14 items.", "6. Timbre reads the total back in Hinglish."],
  "Here is how it works. The browser records the order. Prisma returns the transcript in Hindi. A small rule based parser reads quantities and items, and builds a bill from a sample catalogue of fourteen items. Timbre then reads the order and total back."),
 ("What it does not do", ["Prices are sample prices, not a real shop's.", "Parser covers a fixed list of items and common number words.", "Prisma misheard 'dedh' once in testing; no accuracy claim.", "Tested with synthetic audio only, not real shop noise.", "", "8 unit tests for the parser pass. Code is publicly available on GitHub."],
  "These are the limits. Prices are sample prices. The parser covers a fixed list of items and common number words. In testing Prisma once misheard the Hindi word dedh, so I make no accuracy claim. I tested with synthetic audio only, not real shop noise. The parser has eight unit tests."),
 ("Next steps", ["Use Evon for open ended orders and corrections.", "Add Timbre voices in more languages: Tamil, Kannada, Bengali.", "Test on noisy telephone audio.", "", "Thank you.  #GnaniAI  #GreatIndianAIInternshipChallenge"],
  "Next, I would use Evon to handle open ended orders and corrections, add more Timbre languages, and test on noisy telephone audio. Thank you."),
]
parts = []
def mk(i, title, lines, narr):
    png = f"vid_build/c{i}.png"; wav = f"vid_build/n{i}.wav"; mp4 = f"vid_build/s{i}.mp4"
    card(png, title, lines); tts(narr, wav); d = dur(wav) + 0.8
    subprocess.run(["ffmpeg","-y","-v","error","-loop","1","-t",f"{d}","-i",png,"-i",wav,"-filter_complex","[1:a]apad[a]","-map","0:v","-map","[a]","-t",f"{d}","-r","25","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-ar","24000",mp4],check=True)
    parts.append(mp4)
for i, s in enumerate(segs): mk(i, *s)
# demo segment: real recording + synthetic order audio at mic_start, read-back after bill shown
m = json.load(open("demo_out/marks.json")); vid = [f for f in os.listdir("demo_out/vid")][0]
a1 = int(m["mic_start"]*1000); a2 = int(m["bill_shown"]*1000)+500
subprocess.run(["ffmpeg","-y","-v","error","-i","demo_out/vid/"+vid,"-i","demo_out/order1_spoken.wav","-i","demo_out/order1_readback.wav",
 "-filter_complex",f"[1:a]aresample=24000,adelay={a1}|{a1}[x];[2:a]aresample=24000,adelay={a2}|{a2}[y];[x][y]amix=inputs=2:normalize=0[a]",
 "-map","0:v","-map","[a]","-t","22","-r","25","-vf","scale=1100:760","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","vid_build/demo.mp4"],check=True)
parts.append("vid_build/demo.mp4")
for i, s in enumerate(tail, start=10): mk(i, *s)
open("vid_build/list.txt","w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i","vid_build/list.txt","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","kirana_demo.mp4"],check=True)
print("duration", dur("kirana_demo.mp4"))
