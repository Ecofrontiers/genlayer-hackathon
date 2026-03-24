# WindfallRouter

Trustless AI inference routing on GenLayer. Validators with different LLMs consensus on where your query should run.

## Built During This Hackathon

GridOracle and SpatialRouter are new Intelligent Contracts built for the GenLayer Bradbury Hackathon (March 2026). [Windfall](https://windfall.ecofrontiers.xyz) is our pre-existing centralized inference gateway, shown as a comparison baseline only.

## The Problem

When a centralized gateway says it routed your inference to the cleanest energy zone, you trust its word. One server, one oracle, one decision. No verification.

WindfallRouter moves the routing decision onchain. Multiple validators independently fetch energy data, independently reason about multi-variable tradeoffs, and reach consensus on the subjective question: given these zone conditions and the agent's preferences, where should this query run?

## How It Works

```
Agent: "green but fast"
  |
  v
SpatialRouter (Intelligent Contract)
  |-- [DETERMINISTIC] Read GridOracle for live zone data
  |-- [NONDET] LLM reasons about routing tradeoff
  |-- [CONSENSUS] Validators with different LLMs agree (or appeal)
  |-- [NONDET] Execute inference in chosen zone
  |-- [DETERMINISTIC] Record reasoning chain onchain
```

**GridOracle** stores verified carbon intensity and renewable % for three zones: Finland (Helsinki), Germany (Nuremberg), and US (Ashburn, Virginia).

**SpatialRouter** uses `run_nondet_unsafe` with LLM reasoning for subjective consensus — validators assess whether the routing choice defensibly satisfies the agent's stated preferences.

## Live Demo

- Frontend: https://frontend-ecofrontiers.vercel.app
- Demo video: TBD

## Run Locally

```bash
# Install GenLayer
npm install -g genlayer
pip install genlayer-test

# Start local environment
genlayer init
genlayer up

# Run tests
pytest tests/ -v

# Deploy contracts
genlayer deploy

# Open frontend
open frontend/index.html
```

## Contracts

| Contract | Purpose | Equivalence Principle |
|----------|---------|----------------------|
| `grid_oracle.py` | Decentralized energy data oracle | Comparative (5% numeric tolerance) |
| `spatial_router.py` | LLM-powered subjective routing | Non-Comparative (defensible choice) |

## Track

**Bradbury Special — Subjective Consensus**

This project demonstrates subjective consensus on a real economic problem. The routing question ("how to weigh green vs fast?") has no formula — it requires judgment. Multiple validators with different LLMs making the same judgment call and reaching consensus is exactly what Optimistic Democracy was designed to verify.

## Team

**Pat Rawson** — [Ecofrontiers SARL](https://ecofrontiers.xyz) (France)

Built Windfall (live spatial inference gateway on Base). Topocurrencies research on geospatially-modified crypto protocols.

## License

MIT
