# Upstream source

This example adapts the OpenAI Cookbook partner example:

**Controlled agentic commerce with AgentCore Payments**

- Upstream directory:
  `https://github.com/openai/openai-cookbook/tree/main/examples/partners/AWS/controlled_agentic_commerce_with_agentcore_payments`
- Raw base used for module download:
  `https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/partners/AWS/controlled_agentic_commerce_with_agentcore_payments/`
- Notebook: `controlled_agentic_commerce.ipynb`
- Authors (upstream): Deepak Jain and Sid Rampally
- License: OpenAI Cookbook content is generally available under the Apache
  License 2.0 / MIT terms applicable to that repository. Retain attribution
  when redistributing adapted modules.
- Snapshot retrieved: 2026-09-23 (exact upstream commit SHA not pinned here;
  re-check the cookbook tree before relying on API shapes outside this local
  sim).

## What was adapted

| Upstream | Omnipay local sim |
|---|---|
| `src/agentic_commerce/*` local modules | `src/omnipay_x402/` |
| OpenAI Agents SDK + scripted `Model` | Tiny scripted `run_supplier_research` (no SDK) |
| AgentCore Payments / Bedrock / AWS e2e | Omitted; `aws_stub.py` returns `SKIPPED` / `NOT_READY` |
| Live testnet USDC | Never enabled (`value_transferred=false`) |

## Intentional omissions

- `agentcore_*.py` modules (payments, session, e2e, infrastructure, runtime, agent, application, learning_model)
- Live wallet connectors, private keys, mnemonics, Coinbase CDP credentials
- Requirements on `openai-agents`, `openai[bedrock]`, `botocore`, `bedrock-agentcore`
