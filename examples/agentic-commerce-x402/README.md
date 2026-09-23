# Agentic commerce x402 (local simulation)

Local-only demonstration of an HTTP **402 Payment Required** → application
approval → synthetic payment proof → receipt / audit loop for ProcureNet /
Omnipay docs.

> **Safety:** This example never moves real funds. There are no live payment
> gates, no AWS credentials, no Bedrock calls, and no wallet private keys.
> `value_transferred=false` always. Live AgentCore Payments is stubbed to
> `SKIPPED` / `NOT_READY`.

Adapted from the OpenAI Cookbook example *Controlled agentic commerce with
AgentCore Payments*. See [SOURCE.md](./SOURCE.md) for attribution.

## Four responsibilities

1. **Agent** — proposes a paid resource fetch (scripted; no live model).
2. **Application policy** — merchant allowlist, purpose, budgets, human approval.
3. **Payment session (simulated)** — `LocalPaymentProcessor` mints synthetic proofs.
4. **Paid API** — `SyntheticMerchant` serves a fictional supplier-risk report.

## Setup

```bash
cd examples/agentic-commerce-x402
uv sync
uv run pytest
```

Or with pip:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"  # or: pip install -e . && pip install pytest
pytest
```

## Quick demo

```python
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from omnipay_x402.demo import build_demo
from omnipay_x402.merchant import RESOURCE_URL
from omnipay_x402.models import ApprovalGrant, PurchaseRequest

now = datetime.now(UTC)
app, merchant, payments = build_demo(now)
purchase = PurchaseRequest(
    request_id="request-001",
    resource_url=RESOURCE_URL,
    purpose="supplier_due_diligence",
    idempotency_key="purchase-001",
)
grant = ApprovalGrant(
    approval_id="approval-001",
    request_id=purchase.request_id,
    resource_url=purchase.resource_url,
    purpose=purchase.purpose,
    maximum_amount=Decimal("0.25"),
    approved_by="synthetic-reviewer",
    approved_at=now,
    expires_at=now + timedelta(minutes=10),
)
result = app.purchase(purchase, approval=grant, now=now)
print(result.status, result.receipt.receipt_id, payments.charge_count)
```

## Mapping to ProcureNet docs

See the Mintlify guide: [`guides/agentic-commerce-x402.mdx`](../../guides/agentic-commerce-x402.mdx).
