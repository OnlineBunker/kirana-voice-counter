"""Turn a Hindi/Hinglish spoken grocery order into an itemised bill.

Rule based on purpose: it runs offline, is easy to test and has no extra model cost.
Prisma gives the transcript (Devanagari or Latin), this module reads it.
"""
import re
import unicodedata
from dataclasses import dataclass, field

# name -> (price per unit in rupees, unit, aliases in Latin and Devanagari)
CATALOG = {
    "Rice": (60, "kg", ["chawal", "rice", "चावल"]),
    "Wheat flour (atta)": (45, "kg", ["atta", "aata", "आटा", "आटे"]),
    "Sugar": (48, "kg", ["cheeni", "chini", "sugar", "चीनी", "शक्कर"]),
    "Toor dal": (150, "kg", ["dal", "daal", "दाल"]),
    "Salt": (22, "kg", ["namak", "salt", "नमक"]),
    "Tea leaves": (110, "pack", ["chai patti", "chai", "tea", "चाय पत्ती", "चायपत्ती", "चाय"]),
    "Maggi noodles": (14, "pack", ["maggi", "noodles", "मैगी", "मैग्गी"]),
    "Biscuits": (10, "pack", ["biscuit", "biscuits", "parle", "बिस्कुट", "बिस्किट"]),
    "Milk": (30, "pack", ["doodh", "milk", "दूध"]),
    "Cooking oil": (180, "litre", ["tel", "oil", "तेल"]),
    "Soap": (35, "pc", ["sabun", "soap", "साबुन"]),
    "Eggs": (8, "pc", ["ande", "anda", "egg", "eggs", "अंडे", "अंडा"]),
    "Bread": (40, "pack", ["bread", "ब्रेड", "डबल रोटी"]),
    "Butter": (58, "pack", ["butter", "makhan", "बटर", "मक्खन"]),
}

NUMBERS = {
    "ek": 1, "एक": 1, "do": 2, "दो": 2, "teen": 3, "तीन": 3, "char": 4, "चार": 4,
    "paanch": 5, "panch": 5, "पाँच": 5, "पांच": 5, "chhe": 6, "che": 6, "छह": 6, "छः": 6,
    "saat": 7, "सात": 7, "aath": 8, "आठ": 8, "nau": 9, "नौ": 9, "das": 10, "दस": 10,
    "dedh": 1.5, "डेढ़": 1.5, "dhai": 2.5, "ढाई": 2.5, "aadha": 0.5, "adha": 0.5, "आधा": 0.5,
    "paav": 0.25, "पाव": 0.25, "sawa": 1.25, "सवा": 1.25,
}
DOZEN = {"dozen", "darjan", "दर्जन"}
UNITS = {
    "kilo": "kg", "kg": "kg", "किलो": "kg", "किग्रा": "kg",
    "gram": "g", "gm": "g", "ग्राम": "g",
    "litre": "litre", "liter": "litre", "लीटर": "litre",
    "packet": "pack", "pack": "pack", "पैकेट": "pack", "पैक": "pack",
    "piece": "pc", "pcs": "pc", "पीस": "pc", "नग": "pc",
    "bottle": "pack", "बोतल": "pack",
}
FILLER = {"bhaiya", "bhaiyya", "भैया", "भय्या", "aur", "और", "de", "dena", "दे", "देना", "do", "भी", "please", "कृपया", "ka", "ki", "ke", "का", "की", "के"}


@dataclass
class Line:
    item: str
    qty: float
    unit: str
    price: float
    amount: float


@dataclass
class Bill:
    transcript: str
    lines: list = field(default_factory=list)
    unmatched: list = field(default_factory=list)

    @property
    def total(self) -> float:
        return round(sum(l.amount for l in self.lines), 2)


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text.lower())
    text = re.sub(r"[।,.!?;:]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _num(token: str):
    if re.fullmatch(r"\d+(\.\d+)?", token):
        return float(token)
    return NUMBERS.get(token)


def _alias_table():
    rows = []
    for name, (_, _, aliases) in CATALOG.items():
        for a in aliases:
            rows.append((_norm(a), name))
    rows.sort(key=lambda r: -len(r[0]))  # longest alias first ("chai patti" before "chai")
    return rows


ALIASES = _alias_table()


def _match_items(tokens):
    """Return [(start, end, item_name)] using the longest alias at each position."""
    found, i = [], 0
    while i < len(tokens):
        hit = None
        for alias, name in ALIASES:
            parts = alias.split(" ")
            if tokens[i:i + len(parts)] == parts:
                hit = (i, i + len(parts), name)
                break
        if hit:
            found.append(hit)
            i = hit[1]
        else:
            i += 1
    return found


def _read_qty(tokens, lo, hi):
    """Find a quantity (and optional unit) inside tokens[lo:hi]. Returns (qty, unit, used_indexes)."""
    qty, unit, used, mult = None, None, [], 1
    for j in range(lo, hi):
        t = tokens[j]
        if t in DOZEN:
            mult = 12
            unit = unit or "pc"
            used.append(j)
        elif t in UNITS and unit is None:
            unit = UNITS[t]
            used.append(j)
        elif _num(t) is not None and qty is None:
            qty = _num(t)
            used.append(j)
    if mult != 1:
        qty = (qty if qty is not None else 1) * mult
    return qty, unit, used


def parse_order(transcript: str) -> Bill:
    tokens = _norm(transcript).split(" ")
    items = _match_items(tokens)
    bill = Bill(transcript=transcript)
    claimed = set()
    for n, (s, e, name) in enumerate(items):
        price, base_unit, _ = CATALOG[name]
        prev_end = items[n - 1][1] if n else 0
        next_start = items[n + 1][0] if n + 1 < len(items) else len(tokens)
        # quantity usually comes before the item: "do kilo chawal". Fall back to after: "chawal do kilo".
        qty, unit, used = _read_qty(tokens, max(prev_end, s - 3), s)
        used = [u for u in used if u not in claimed]
        if qty is None:
            qty, unit, used = _read_qty(tokens, e, min(next_start, e + 3))
            used = [u for u in used if u not in claimed]
        claimed.update(used)
        if qty is None:
            qty = 1
        # "adha kilo" / "dedh kilo" read as 0.5 / 1.5 kg
        unit = unit or base_unit
        billed_qty = qty
        if unit == "g" and base_unit == "kg":
            billed_qty = qty / 1000
        elif unit == "kg" and base_unit in ("pack", "pc"):
            unit = base_unit
        bill.lines.append(Line(name, qty, unit, price, round(billed_qty * price, 2)))
    for j, t in enumerate(tokens):
        if j in claimed or t in FILLER or t in UNITS or _num(t) is not None:
            continue
        if not any(s <= j < e for s, e, _ in items):
            bill.unmatched.append(t)
    return bill


def _fmt(q: float) -> str:
    return str(int(q)) if float(q).is_integer() else str(q)


def spoken_summary(bill: Bill) -> str:
    """Short Hinglish read-back for Timbre."""
    if not bill.lines:
        return "Maaf kijiye, mujhe koi saaman samajh nahi aaya. Dobara boliye."
    parts = [f"{_fmt(l.qty)} {l.unit} {l.item.split(' (')[0]}" for l in bill.lines]
    return "Aapka order: " + ", ".join(parts) + f". Total {_fmt(bill.total)} rupaye. Dhanyavaad."
