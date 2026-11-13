"""Records a real run of the app in headless Chrome. The microphone is a fake device that plays
a Timbre-generated Hinglish order (demo_out/order1_spoken.wav), so the whole path is real:
browser mic -> ffmpeg -> Prisma -> parser -> bill -> Timbre read-back."""
import json, os, subprocess, sys, time
from playwright.sync_api import sync_playwright

WAV = os.path.abspath("demo_out/order1_spoken.wav")
env = dict(os.environ)
srv = subprocess.Popen([sys.executable, "app.py"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)
marks = {}
try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True, args=[
            "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
            f"--use-file-for-fake-audio-capture={WAV}", "--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        ctx = b.new_context(viewport={"width": 1100, "height": 760}, record_video_dir="demo_out/vid",
                            record_video_size={"width": 1100, "height": 760}, permissions=["microphone"])
        page = ctx.new_page(); t0 = time.time()
        page.goto("http://localhost:8000"); page.wait_for_timeout(2500)
        marks["mic_start"] = time.time() - t0
        page.click("#mic"); page.wait_for_timeout(5600)       # fake mic plays the order once (~4.3 s)
        page.click("#mic"); marks["mic_stop"] = time.time() - t0
        page.wait_for_function("document.querySelectorAll('#rows tr').length>0", timeout=40000)
        marks["bill_shown"] = time.time() - t0
        page.screenshot(path="demo_out/shot_bill.png")
        page.wait_for_timeout(7000)                            # time for the read-back
        page.fill("#typed", "dedh kilo cheeni aur ek litre tel")
        page.click("#go"); page.wait_for_timeout(5000)
        page.screenshot(path="demo_out/shot_typed.png")
        marks["end"] = time.time() - t0
        ctx.close(); b.close()
finally:
    srv.terminate()
json.dump(marks, open("demo_out/marks.json", "w"), indent=1); print(marks)
