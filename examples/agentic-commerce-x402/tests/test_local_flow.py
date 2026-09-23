"""Local x402 happy path, denial, and fabricated-receipt rejection tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from omnipay_x402.agent import (
    PurchaseResultRecorder,
    SupplierResearchOutput,
    run_supplier_research,
    validate_supplier_research_output,
)
from omnipay_x402.application import CommerceApplication
from omnipay_x402.aws_stub import live_agentcore_status
from omnipay_x402.codec import encode_model
from omnipay_x402.errors import AgentResultInvalid, PolicyDenied
from omnipay_x402.merchant import (
    PAYMENT_REQUIRED_HEADER,
    PAYMENT_SIGNATURE_HEADER,
    RESOURCE_URL,
    SyntheticMerchant,
)
from omnipay_x402.models import (
    ApprovalGrant,
    AuditEventType,
    CommercePolicy,
    PurchaseRequest,
)
from omnipay_x402.payments import LocalPaymentProcessor
from omnipay_x402.policy import PolicyEngine
from omnipay_x402.tool import build_x402_fetch_tool
from omnipay_x402 import VALUE_TRANSFERRED

NOW = datetime(2026, 7, 30, 16, 0, tzinfo=UTC)


def make_system(
    *,
    price: Decimal = Decimal("0.25"),
    request_limit: Decimal = Decimal("0.50"),
    run_limit: Decimal = Decimal("1.00"),
    threshold: Decimal = Decimal("0.10"),
    session_expires_at: datetime | None = None,
) -> tuple[CommerceApplication, SyntheticMerchant, LocalPaymentProcessor]:
    payments = LocalPaymentProcessor()
    merchant = SyntheticMerchant(payments, price=price, now=NOW)
    policy = PolicyEngine(
        CommercePolicy(
            allowed_merchants=frozenset({"merchant.invalid"}),
            allowed_purposes=frozenset({"supplier_due_diligence"}),
            per_request_limit=request_limit,
            per_run_limit=run_limit,
            approval_threshold=threshold,
            session_expires_at=(session_expires_at or NOW + timedelta(minutes=15)),
        )
    )
    app = CommerceApplication(
        client=merchant.client(),
        policy=policy,
        payments=payments,
    )
    return app, merchant, payments


def request(
    *,
    request_id: str = "request-001",
    resource_url: str = RESOURCE_URL,
    purpose: str = "supplier_due_diligence",
    idempotency_key: str = "purchase-001",
) -> PurchaseRequest:
    return PurchaseRequest(
        request_id=request_id,
        resource_url=resource_url,
        purpose=purpose,
        idempotency_key=idempotency_key,
    )


def approval(
    purchase: PurchaseRequest,
    *,
    maximum_amount: Decimal = Decimal("0.25"),
    expires_at: datetime | None = None,
) -> ApprovalGrant:
    return ApprovalGrant(
        approval_id=f"approval-{purchase.request_id}",
        request_id=purchase.request_id,
        resource_url=purchase.resource_url,
        purpose=purchase.purpose,
        maximum_amount=maximum_amount,
        approved_by="synthetic-reviewer",
        approved_at=NOW,
        expires_at=expires_at or NOW + timedelta(minutes=10),
    )


def test_value_transferred_is_always_false() -> None:
    assert VALUE_TRANSFERRED is False
    status = live_agentcore_status()
    assert status["status"] == "SKIPPED"
    assert status["reason"] == "NOT_READY"
    assert status["value_transferred"] is False
    assert status["network_calls"] is False


def test_approved_purchase_completes_full_402_sequence() -> None:
    """Happy path: 402 → approve → synthetic proof → receipt/audit."""

    app, merchant, payments = make_system()
    purchase = request()

    result = app.purchase(purchase, approval=approval(purchase), now=NOW)

    assert result.status == "completed"
    assert result.receipt.amount == Decimal("0.25")
    assert result.authorization.requires_human_approval is True
    assert result.report.report_id == "SYNTH-SUPPLIER-RISK-001"
    assert merchant.request_count == 2
    assert merchant.fulfilled_count == 1
    assert payments.charge_count == 1
    assert [event.event_type for event in result.audit_events] == [
        AuditEventType.RESOURCE_REQUESTED,
        AuditEventType.PAYMENT_REQUIRED,
        AuditEventType.AUTHORIZATION_CHECKED,
        AuditEventType.PAYMENT_ATTEMPTED,
        AuditEventType.PROOF_CREATED,
        AuditEventType.MERCHANT_RETRY,
        AuditEventType.CONTENT_RETURNED,
    ]


def test_missing_human_approval_is_denied_before_payment() -> None:
    """Denial without approval: policy blocks before synthetic payment."""

    app, merchant, payments = make_system()

    with pytest.raises(PolicyDenied) as exc_info:
        app.purchase(request(), now=NOW)

    assert exc_info.value.code == "human_approval_required"
    assert merchant.request_count == 1
    assert payments.charge_count == 0


def test_application_validation_rejects_fabricated_receipt() -> None:
    """Fabricated receipt rejection: agent output must match app evidence."""

    app, _, _ = make_system()
    purchase = request()
    completed = app.purchase(purchase, approval=approval(purchase), now=NOW)
    fabricated = SupplierResearchOutput(
        status=completed.status,
        report_id=completed.report.report_id,
        supplier=completed.report.supplier,
        signals=completed.report.signals,
        disclaimer=completed.report.disclaimer,
        receipt_id="receipt-fabricated",
        amount=str(completed.receipt.amount),
        currency=completed.receipt.currency,
        requires_human_approval=completed.authorization.requires_human_approval,
    )

    with pytest.raises(AgentResultInvalid) as exc_info:
        validate_supplier_research_output(
            fabricated,
            PurchaseResultRecorder(results=[completed]),
        )

    assert exc_info.value.code == "agent_output_mismatch"
    assert "receipt_id" in str(exc_info.value)


def test_scripted_agent_run_matches_application_evidence() -> None:
    app, merchant, payments = make_system()
    purchase = request(request_id="request-agent-001", idempotency_key="purchase-agent-001")

    result = run_supplier_research(
        app,
        request_id=purchase.request_id,
        idempotency_key=purchase.idempotency_key,
        approval=approval(purchase),
        now=NOW,
    )

    assert result.output.receipt_id == result.purchase.receipt.receipt_id
    assert merchant.request_count == 2
    assert payments.charge_count == 1


def test_merchant_rejects_unrecognized_proof() -> None:
    _, merchant, payments = make_system()
    response = merchant.client().get(
        RESOURCE_URL,
        headers={PAYMENT_SIGNATURE_HEADER: encode_model(merchant.payment_required)},
    )

    assert response.status_code == 402
    assert PAYMENT_REQUIRED_HEADER in response.headers
    assert merchant.invalid_proof_count == 1
    assert payments.charge_count == 0


def test_agents_tool_has_prebound_authority_and_expected_name() -> None:
    app, _, _ = make_system()
    purchase = request()
    tool = build_x402_fetch_tool(
        app,
        request_id=purchase.request_id,
        idempotency_key=purchase.idempotency_key,
        approval=approval(purchase),
    )

    assert tool.name == "x402_fetch"
