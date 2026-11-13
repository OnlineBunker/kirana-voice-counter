# Kirana Voice Counter - solution pitch (1 page)

**Entry:** The Great Indian AI Internship Challenge, solo. Yash Dhankhar, BTech, Rishihood University.

**Problem.** Small shopkeepers take orders in Hindi and Hinglish while serving other customers. Typing each item
into a billing app is slow and error prone.

**Solution.** Say the order. Get an itemised bill. Hear it read back so the customer can confirm.
Example: "bhaiya do kilo chawal, ek packet Maggi aur teen chai patti" becomes 2 kg rice, 1 pack Maggi, 3 packs tea, total Rs 464.

**Gnani AI models used.**
- Prisma v3.0 (speech to text, language auto-detect): transcribes the spoken order. Contribution: the only speech understanding step.
- Timbre v2.5 (text to speech, `hi-en` Hinglish): reads the order and total back, and generated the synthetic voice used in the demo.

**Who uses it.** Kirana and small retail shops, home delivery counters, anyone who bills by voice.

**Contribution.** Solo: parser, server, UI, tests, demo.

**What was verified.** 8 parser unit tests pass. A real run of the app in Chrome (synthetic Hinglish order as the microphone)
returned the correct 3-line bill. Demo audio is synthetic, prices are sample prices, the catalogue has 14 items,
and there is no accuracy claim. Prisma once misheard "dedh" in testing.

**Next.** Use Evon for open ended orders and corrections, more Timbre languages, noisy telephone audio.

Code: see README.md. Demo: kirana_demo.mp4.
