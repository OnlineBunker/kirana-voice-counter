import unittest
from kirana import parse_order, spoken_summary


class ParseOrder(unittest.TestCase):
    def test_devanagari_from_prisma(self):
        b = parse_order("भैया दो किलो चावल, एक पैकेट मैगी और तीन चाय पत्ती दे देना।")
        got = [(l.item, l.qty) for l in b.lines]
        self.assertEqual(got, [("Rice", 2), ("Maggi noodles", 1), ("Tea leaves", 3)])
        self.assertEqual(b.total, 2 * 60 + 14 + 3 * 110)

    def test_latin_hinglish(self):
        b = parse_order("bhaiya dedh kilo cheeni aur ek litre tel")
        self.assertEqual([(l.item, l.qty) for l in b.lines], [("Sugar", 1.5), ("Cooking oil", 1)])
        self.assertEqual(b.total, 1.5 * 48 + 180)

    def test_quantity_after_item(self):
        b = parse_order("atta 5 kilo")
        self.assertEqual((b.lines[0].item, b.lines[0].qty, b.lines[0].amount), ("Wheat flour (atta)", 5, 225))

    def test_grams(self):
        b = parse_order("500 gram namak")
        self.assertEqual(b.lines[0].amount, 11)

    def test_dozen_eggs(self):
        b = parse_order("ek dozen ande")
        self.assertEqual(b.lines[0].amount, 96)

    def test_chai_patti_not_split(self):
        b = parse_order("do chai patti")
        self.assertEqual([l.item for l in b.lines], ["Tea leaves"])

    def test_unknown_items_reported(self):
        b = parse_order("ek maggi aur ek laptop")
        self.assertIn("laptop", b.unmatched)

    def test_no_items(self):
        b = parse_order("namaste kaise ho")
        self.assertFalse(b.lines)
        self.assertIn("Maaf", spoken_summary(b))


if __name__ == "__main__":
    unittest.main()
