# WindfallRouter Demo Video — 2 minutes

## Setup Before Recording

- Open https://frontend-ecofrontiers.vercel.app (defaults to Bradbury)
- History should have 3+ entries from different priority configs
- Open https://explorer-bradbury.genlayer.com in another tab
- Pre-authenticate everything, no login screens

## Beat 1: The Problem (20s)

[Screen: WindfallRouter frontend, pause on the node cards]

VOICEOVER:
"When a centralized gateway routes your AI inference, you trust its word. It picks the model. It picks the data center. One server, one decision, no verification."

[Pause on the comparison callout: "Centralized gateway: one server picks the route. Trust us. WindfallRouter: 5 validators independently re-reason. Verify it onchain."]

## Beat 2: The Nodes (15s)

[Point to the 3 node cards: FI/DeepSeek, DE/Llama, US/Claude]

VOICEOVER:
"Three inference nodes. Finland runs DeepSeek — cheapest, greenest at 45 grams CO2, but highest latency. Germany runs Llama — balanced. Virginia runs Claude Sonnet — fastest, smartest, but dirtiest at 420 grams CO2."

## Beat 3: Live Routing (45s)

[Click "Smartest" preset — sliders move to L0 Q10 C0]

VOICEOVER:
"I want the smartest model, don't care about carbon or latency."

[Type prompt: "Explain why transformer architectures work". Click Route Inference.]

"Five validators on the Bradbury testnet independently evaluate this. The leader picks a node. Each validator checks: is this choice defensible given my priorities?"

[Result appears: US / Claude Sonnet 4, with validator vote circles]

"US, Claude Sonnet 4. All five validators agreed. Quality score 9 out of 10, 45 milliseconds latency."

[Now click "Greenest" preset — sliders move to L0 Q0 C10]
[Type prompt: "What is the carbon footprint of AI training?". Click Route Inference.]

"Same router, different priorities. Now I want the greenest possible."

[Result appears: FI / DeepSeek V3]

"Finland, DeepSeek V3. 45 grams CO2 — 89% less carbon than Virginia. The router made a completely different decision because the priorities changed. And validators verified both."

## Beat 4: The Consensus (15s)

[Point to the validator vote circles — green checkmarks]

VOICEOVER:
"Each circle is a validator. Green checkmark means they independently verified the routing choice is defensible. This isn't rubber-stamping JSON structure — they check that the reasoning references the chosen node and the stated priorities."

[Click "View on Explorer" link]

"Every decision is onchain. Verifiable on the Bradbury block explorer."

## Beat 5: Close (10s)

[Back to frontend, hold on the WindfallRouter header]

VOICEOVER:
"WindfallRouter. Three dimensions — latency, quality, carbon. Three nodes. Five validators. One verifiable routing decision. Subjective consensus on a real inference routing problem."

---

## Recording Notes

- QuickTime screen recording or OBS, 1920x1080
- Voiceover can be recorded separately and synced in iMovie
- Keep mouse movements slow and deliberate
- If routing takes >30s, cut during "Validators reasoning..." spinner and resume when result appears
- Total target: 1:50–2:00
- The two live routing demos are the core — make sure both succeed before recording (test first)
