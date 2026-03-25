# WindfallRouter

Trustless AI inference routing on GenLayer. Five validators independently reason about which node should handle your query — and reach subjective consensus on the tradeoff between latency, model quality, and carbon impact.

## The Problem

When a centralized inference gateway routes your query, you trust its word. It picks the model. It picks the data center. One server, one decision. No verification.

But inference routing involves real tradeoffs. A fast node runs a premium model at high carbon cost. A green node runs a cheaper model with higher latency. An agent that says "balance quality and carbon" is asking for a judgment no formula can resolve.

WindfallRouter makes this judgment verifiable. Multiple validators with different LLMs independently evaluate the same node data and priorities, then assess whether the leader's routing choice is *defensible*. Not identical — defensible. That's subjective consensus.

## How It Works

```
Agent sets priorities: latency=2, quality=8, carbon=6
  |
  v
SpatialRouter (Intelligent Contract)
  |-- [DETERMINISTIC] Load node data (model, latency, carbon, quality score)
  |-- [NONDET] Leader LLM selects a node given task + priorities
  |-- [CONSENSUS] Validators verify: is this choice defensible?
  |-- [DETERMINISTIC] Record routing decision + reasoning onchain
```

### Three Nodes, Three Tradeoffs

| Node | Model | Quality | Latency | Carbon |
|------|-------|---------|---------|--------|
| **FI** Helsinki | DeepSeek V3 | 7/10 | 145ms | 45 gCO2/kWh |
| **DE** Nuremberg | Llama 3.3 70B | 6/10 | 89ms | 302 gCO2/kWh |
| **US** Ashburn, VA | Claude Sonnet 4 | 9/10 | 45ms | 420 gCO2/kWh |

Agents set three priority sliders (0-10 each): **latency**, **quality**, **carbon**. The router weighs these against node capabilities and selects the best fit. Different priority configs produce different routing decisions — all verified by consensus.

### Validator Verification

The validator checks that the leader's routing choice is semantically coherent: the chosen node is valid, and the reasoning references the selected zone, model, or relevant priority dimensions. On production infrastructure, this extends to full LLM re-reasoning where each validator independently assesses defensibility.

## Contracts

| Contract | Purpose | Equivalence Principle |
|----------|---------|----------------------|
| `grid_oracle.py` | Energy data oracle with live API feeds | Comparative (5% tolerance) |
| `spatial_router_simple.py` | Production router with 3 priority sliders | Non-Comparative (defensible choice) |
| `spatial_router.py` | Full version with cross-contract oracle reads | Non-Comparative (defensible choice) |

### Deployed on Bradbury Testnet

- GridOracle: [`0x941948E5ecf03647D58D7C6A090447c9B6973652`](https://explorer-bradbury.genlayer.com/address/0x941948E5ecf03647D58D7C6A090447c9B6973652)
- SpatialRouterSimple: [`0x29c98da945477EDA0892aFBD54EaA979c1e3AF89`](https://explorer-bradbury.genlayer.com/address/0x29c98da945477EDA0892aFBD54EaA979c1e3AF89)

### Security

- Owner-gated admin functions (zone updates, oracle address)
- Node validation in validators (must be FI/DE/US)
- Input length limits on priorities and prompts
- Falsy-value bug fix on carbon intensity API (0 is valid, not missing)

## Live Demo

- **Frontend**: https://frontend-ecofrontiers.vercel.app
- **Explorer**: https://explorer-bradbury.genlayer.com
- **Demo video**: TBD

## Run Locally

```bash
npm install -g genlayer
pip install genlayer-test

# Deploy to Bradbury testnet (needs funded account)
DEPLOYER_KEY=0x... node deploy/deploy-bradbury.mjs

# Deploy to studionet
node deploy/deploy-studionet.mjs

# Run tests
pytest tests/ -v

# Open frontend
open frontend/index.html
```

## What We Learned

1. **Structural validation is not consensus.** Checking `"zone" in data` means the validator is rubber-stamping the leader. Real subjective consensus requires the validator to independently verify the reasoning is coherent.

2. **"Defensible" is the right standard.** Requiring validators to reach the same answer defeats the purpose — different LLMs should be allowed to disagree on close calls. The question is whether the leader's answer is *defensible*, not *optimal*.

3. **Validator LLM re-reasoning times out on testnet.** Calling `exec_prompt` inside the validator function causes 80% consensus failure on Bradbury due to timeouts. Semantic validation (checking reasoning references the chosen node and priorities) is reliable and still meaningful.

4. **The routing question produces genuinely different answers.** Same contract, same nodes, different priority sliders → different routing decisions. "Smartest" routes to US/Claude. "Greenest" routes to FI/DeepSeek. "Balanced" is the subjective call where validators might disagree.

## Track

**Bradbury Special — Subjective Consensus**

This project demonstrates subjective consensus on a real economic problem. Inference routing involves multi-variable tradeoffs (latency vs quality vs carbon) that have no formula. Multiple validators making independent judgment calls and verifying defensibility — rather than requiring identical answers — is what Optimistic Democracy was designed for.

## Team

**Pat Rawson** — [Ecofrontiers SARL](https://ecofrontiers.xyz) (France)

Built [Windfall](https://windfall.ecofrontiers.xyz), a live spatial inference gateway on Base. Topocurrencies research on geospatially-modified crypto protocols.

## License

MIT
