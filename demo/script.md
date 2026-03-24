# WindfallRouter Demo Video — 2 minutes

## Setup Before Recording

- Open https://frontend-ecofrontiers.vercel.app
- Select "Bradbury Testnet" from dropdown
- Have 3 routing decisions already in history (greenest, cheapest, balanced)
- Open https://explorer-bradbury.genlayer.com in another tab
- Pre-authenticate everything, no login screens during recording

## Beat 1: The Problem (20s)

[Screen: Windfall dashboard or just the WindfallRouter frontend]

VOICEOVER:
"When a centralized gateway routes your AI inference to the greenest data center, you trust its word. One server made the decision. One oracle signed the attestation. No way to verify."

[Pause on the comparison callout box: "Centralized: Trust us. WindfallRouter: Verify it."]

## Beat 2: The Solution — Live Demo (50s)

[Screen: WindfallRouter frontend on Bradbury Testnet. Zone cards showing FI=45, DE=302, US=420]

VOICEOVER:
"WindfallRouter moves the routing decision onchain. Three energy zones — Finland at 45 grams CO2, Germany at 302, Virginia at 420. Real data from the GridOracle contract."

[Select "Green but fast" from dropdown. Click Route Inference.]

"I'm asking: route my inference somewhere green but fast. Watch what happens."

[Loading spinner: "Validators reasoning..."]

"Five validators — each running a different LLM — independently evaluate this question. The leader picks a zone. Then each validator asks its own LLM: is this choice defensible?"

[Result appears: Routed to FI, with reasoning]

"Finland. The leader chose it for the lowest carbon and highest renewable percentage. The validators independently confirmed it's a defensible choice. Not identical reasoning — defensible reasoning."

[Point to "Subjective Consensus" bar and "View on Explorer" link]

## Beat 3: Different Preferences, Different Decisions (30s)

[Click History tab. Show 3 previous routing decisions.]

VOICEOVER:
"Now watch what happens with different preferences."

[Click on "cheapest" history row — modal opens]

"When the agent says cheapest, the validators reason differently. The LLM weighs cost over carbon and may route to a different zone entirely."

[Close modal. Click on "balanced" row.]

"Balanced gives yet another answer. The point is: this isn't a formula. It's judgment. And that judgment is verified by independent consensus — which is exactly what GenLayer's Optimistic Democracy was built to do."

## Beat 4: What Makes This Real (10s)

[Click "View on Explorer" link — show Bradbury explorer with the tx]

VOICEOVER:
"Every routing decision lives onchain on Bradbury testnet. The zone, the reasoning, the consensus — all verifiable."

## Beat 5: Close (10s)

[Back to frontend. Show GitHub link in header.]

VOICEOVER:
"WindfallRouter. Trustless spatial inference routing. Validators don't rubber-stamp — they re-reason. That's subjective consensus on a real economic problem."

[Hold on the WindfallRouter logo for 2 seconds. End.]

---

## Recording Notes

- Use QuickTime screen recording or OBS
- 1920x1080, no webcam overlay needed
- Voiceover can be recorded separately and synced
- Keep mouse movements slow and deliberate
- If a routing takes too long (>30s), cut and resume after consensus
- Total target: 1:50–2:00
