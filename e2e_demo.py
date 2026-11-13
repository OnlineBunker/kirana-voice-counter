"""End-to-end check using only Gnani APIs: Timbre speaks an order, Prisma transcribes it,
the parser builds the bill, Timbre reads it back, Prisma transcribes the read-back.
Writes demo_out/*.wav and demo_out/result.json. Uses about 4 API calls per order."""
import json, os, sys
from pathlib import Path
import gnani
from kirana import parse_order, spoken_summary

ORDERS = [
    "bhaiya do kilo chawal, ek packet Maggi aur teen chai patti de dena",
    "dedh kilo cheeni, ek litre tel aur ek dozen ande chahiye",
]
out = Path("demo_out"); out.mkdir(exist_ok=True)
results = []
for i, text in enumerate(ORDERS if len(sys.argv) < 2 else sys.argv[1:], 1):
    wav = gnani.speak(text); (out / f"order{i}_spoken.wav").write_bytes(wav)
    meta = gnani.transcribe(wav)
    bill = parse_order(meta["transcript"])
    summary = spoken_summary(bill)
    back = gnani.speak(summary); (out / f"order{i}_readback.wav").write_bytes(back)
    check = gnani.transcribe(back)["transcript"]
    results.append({"spoken_text": text, "prisma_transcript": meta["transcript"],
                    "lines": [(l.item, l.qty, l.unit, l.amount) for l in bill.lines],
                    "total": bill.total, "readback_text": summary, "readback_transcribed": check})
(out / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
print(json.dumps(results, ensure_ascii=False, indent=2))
