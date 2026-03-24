# GenLayer Hackathon — Bradbury Testnet

Hackathon project for GenLayer Bradbury Hackathon (Mar 20 - Apr 3, 2026).

## What is GenLayer

"The first Intelligent Blockchain" — smart contracts that natively access the internet, use LLMs, and make subjective (non-deterministic) decisions. Python-based contracts, not Solidity.

## Core Concepts

**Intelligent Contracts:** Python smart contracts that can:
- Call LLMs during execution
- Access web data
- Make subjective decisions (not just deterministic logic)
- Use vector storage

**Optimistic Democracy:** Consensus mechanism where:
- Multiple validators (5, scaling to 1000) independently run the contract
- Each validator can use different LLMs
- Majority agreement = valid transaction
- Appeal mechanism for contested results
- Rewards for majority voters, penalties for minority

**Equivalence Principle:** Contracts must be written so different LLMs produce equivalent outputs. The consensus works because the same contract run by different models should reach the same conclusion.

**Greyboxing:** Validators can apply transformations before LLM calls — input filtering, security hardening, cost optimization.

**Model Routing:** Validators choose which LLM to use per contract. Fine-tuned small models for frequent contracts, powerful models for appeals.

## Dev Stack

- **Language:** Python (Intelligent Contracts)
- **SDK:** GenLayer CLI + GenLayerJS (frontend) + GenLayerPY
- **IDE:** GenLayer Studio (local sandbox)
- **Install:** `npm install -g genlayer && genlayer init && genlayer up`
- **Prerequisites:** Docker 26+, Node.js 18+
- **Examples:** github.com/yeagerai/genlayer-studio/examples/contracts/

## Hackathon Tracks

1. Agentic Economy Infrastructure
2. AI Governance
3. Prediction Markets & P2P Betting
4. AI Gaming
5. Onchain Justice
6. Future of Work
7. Bradbury Special (Subjective Consensus research)

## Requirements

- Must use Intelligent Contract with Optimistic Democracy + Equivalence Principle
- Deadline: Apr 3, 2026
- Judging: Apr 3-10
- Demo Day: Apr 10

## Key Differentiator for Us

GenLayer validators do MODEL ROUTING — choosing which LLM to use per contract. This is literally what Windfall does (spatial model routing). The validator layer IS an inference routing problem.
