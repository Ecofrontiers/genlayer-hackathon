# WindfallRouter Demo Script (2 min)

## Beat 1: Centralized Baseline (30s)

[Screen: Windfall dashboard at windfall.ecofrontiers.xyz]

"Every AI inference request today routes through a centralized gateway. When Windfall says it routed your query to Finland at 45 grams of CO2 per kilowatt-hour, you get this attestation on Base."

[Show EAS attestation on BaseScan]

"Signed by us. Our word. Trust us."

## Beat 2: Same Request on GenLayer (50s)

[Screen: WindfallRouter frontend]

"Same request. But now the routing decision happens onchain."

[Type preferences: "green but fast"]
[Type prompt: "What is the state of renewable energy in Europe?"]
[Click Route Inference]

"Watch what happens. GridOracle fetches live energy data from the UK Carbon Intensity API and Windfall's energy endpoint. Three zones: Great Britain at 263, Germany at 302, Finland at 45 grams CO2."

[Zone cards populate with live data]

"Now the SpatialRouter asks the LLM: given these conditions and the agent's preference for green but fast, where should this run?"

[Reasoning panel appears]

"Finland. Lowest carbon at 45 grams, 82% renewable. And this wasn't our decision — five validators with different models independently reached the same conclusion through Optimistic Democracy."

[Consensus bar fills]

## Beat 3: Why This Matters (25s)

"A centralized gateway can lie about routing. It can claim green while routing dirty. On GenLayer, five validators independently check. The subjective question — how to weigh green versus fast — gets a verified answer through consensus."

[Point at provenance history table]

"Every routing decision is recorded onchain with the full reasoning chain. Not just where it routed — why."

## Beat 4: Close (15s)

"Windfall routes spatially on Base today. GenLayer makes it honest. GridOracle is open infrastructure — any contract on GenLayer can query live energy data. SpatialRouter proves that subjective AI decisions can reach trustless consensus."

[Show README / GitHub link]
