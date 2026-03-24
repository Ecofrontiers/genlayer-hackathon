# WindfallRouter

Trustless AI inference routing on GenLayer. Validators with different LLMs independently reason about where your query should run — and reach consensus on the subjective tradeoff.

## The Problem

When a centralized gateway says it routed your inference to the cleanest energy zone, you trust its word. One server, one oracle, one decision. No verification.

But "greenest" is subjective. An agent that says "green but fast" is asking for a tradeoff no formula can resolve. It requires judgment — and judgment should be verifiable.

WindfallRouter moves this decision onchain. Multiple validators with different LLMs independently evaluate the same zone data and preferences, make their own routing judgment, then assess whether the leader's choice is *defensible*. Not identical — defensible. That's subjective consensus.

## How It Works

```
Agent: "green but fast"
  |
  v
SpatialRouter (Intelligent Contract)
  |-- [DETERMINISTIC] Read GridOracle for zone data (carbon, renewable %)
  |-- [NONDET] Leader LLM reasons about routing tradeoff
  |-- [NONDET] Validator LLMs independently assess: "Is this defensible?"
  |-- [CONSENSUS] Optimistic Democracy: majority agrees or appeals
  |-- [DETERMINISTIC] Record routing decision + reasoning onchain
```

### The Validator Re-Reasoning Pattern

Most GenLayer examples validate structure ("does this JSON have the right keys?"). WindfallRouter validates *judgment*. The validator runs its own LLM call:

> "The leader chose Finland because it has the lowest carbon at 45 gCO2/kWh. Given these zone conditions and the agent's preference for 'green but fast', is this a defensible choice?"

Different LLMs may weigh the tradeoff differently. A validator using GPT-4 might agree Finland is defensible even if it would have chosen Germany. Another using Claude might disagree if it thinks "fast" should dominate. When they disagree enough, the appeal mechanism escalates to more validators — exactly how Optimistic Democracy is designed to work.

## Contracts

| Contract | Purpose | Equivalence Principle |
|----------|---------|----------------------|
| `grid_oracle.py` | Decentralized energy data oracle | Comparative (5% numeric tolerance on carbon intensity) |
| `spatial_router_simple.py` | LLM-powered subjective routing (hardcoded zones) | Non-Comparative (defensible choice via validator re-reasoning) |
| `spatial_router.py` | Full version with cross-contract oracle reads | Non-Comparative (defensible choice via validator re-reasoning) |

### Security

- Owner-gated admin functions (zone updates, oracle address)
- Zone validation in validators (must be FI/DE/US/GB)
- Input length limits on preferences and prompts
- Falsy-value bug fix on carbon intensity API (0 is valid, not missing)

## Architecture

**GridOracle** stores verified carbon intensity (gCO2/kWh) and renewable percentage for energy zones:
- FI (Helsinki) — 45 gCO2, 82% renewable
- DE (Nuremberg) — 302 gCO2, 55% renewable
- US (Ashburn, VA) — 420 gCO2, 22% renewable

Data sources: UK Carbon Intensity API (no auth), Windfall energy endpoint, hardcoded fallback (owner-gated).

**SpatialRouter** uses `gl.vm.run_nondet_unsafe` with two non-deterministic stages:
1. **Leader reasoning**: LLM selects a zone given data + preferences
2. **Validator assessment**: Different LLM evaluates if the leader's choice is defensible

This pattern — leader proposes, validator assesses defensibility — maps naturally to any subjective routing problem where multiple reasonable answers exist.

## Live Demo

- **Frontend**: https://frontend-ecofrontiers.vercel.app
- **Explorer**: https://explorer-bradbury.genlayer.com
- **Demo video**: TBD

## Run Locally

```bash
npm install -g genlayer
pip install genlayer-test

# Deploy to studionet
node deploy/deploy-studionet.mjs

# Deploy to Bradbury testnet (needs funded account)
DEPLOYER_KEY=0x... node deploy/deploy-bradbury.mjs

# Run tests
pytest tests/ -v

# Open frontend
open frontend/index.html
```

## What We Learned

1. **Structural validation is not consensus.** Checking `"zone" in data` means the validator is rubber-stamping the leader. Real subjective consensus requires the validator to independently reason about the same question.

2. **"Defensible" is the right standard for subjective decisions.** Requiring validators to reach the same answer defeats the purpose — different LLMs should be allowed to disagree on close calls. The question is whether the leader's answer is *defensible*, not *optimal*.

3. **Cross-contract calls fail on studionet.** `gl.get_contract_at().view()` breaks consensus on the development network. SpatialRouterSimple works around this by hardcoding zone data. The full SpatialRouter with oracle reads is designed for Bradbury.

4. **Zero is falsy in Python but valid for carbon intensity.** `actual or forecast` silently falls through when `actual == 0`. Had to use explicit `if actual is not None` checks.

## Track

**Bradbury Special — Subjective Consensus**

This project demonstrates subjective consensus on a real economic problem. The routing question ("how to weigh green vs fast?") has no formula. It requires judgment. Multiple validators with different LLMs making independent judgment calls — and reaching consensus on defensibility rather than identity — is what Optimistic Democracy was designed to verify.

## Team

**Pat Rawson** — [Ecofrontiers SARL](https://ecofrontiers.xyz) (France)

Built [Windfall](https://windfall.ecofrontiers.xyz), a live spatial inference gateway on Base. Topocurrencies research on geospatially-modified crypto protocols.

## License

MIT
