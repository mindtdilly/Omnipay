"""Scripted one-tool supplier research loop (no live model, no Agents SDK)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .application import CommerceApplication
from .errors import AgentResultInvalid
from .models import ApprovalGrant, PurchaseResult
from .tool import X402FetchTool, build_x402_fetch_tool

DEFAULT_RESOURCE_URL = (
    "https://merchant.invalid/reports/SYNTH-SUPPLIER-RISK-001"
)
DEFAULT_PURPOSE = "supplier_due_diligence"


class SupplierResearchOutput(BaseModel):
    """Typed, non-authoritative summary proposed by the scripted agent."""

    model_config = ConfigDict(frozen=True)

    status: Literal["completed"]
    report_id: Literal["SYNTH-SUPPLIER-RISK-001"]
    supplier: Literal["Northstar Components"]
    signals: tuple[str, ...]
    disclaimer: str
    receipt_id: str
    amount: Literal["0.25"]
    currency: Literal["USDC"]
    requires_human_approval: bool


@dataclass
class PurchaseResultRecorder:
    """Application-owned, per-run record of completed tool purchases."""

    results: list[PurchaseResult] = field(default_factory=list)

    def record(self, result: PurchaseResult) -> None:
        self.results.append(result)


@dataclass(frozen=True)
class SupplierResearchRun:
    """Agent proposal paired with the application evidence that validated it."""

    output: SupplierResearchOutput
    purchase: PurchaseResult


@dataclass
class ScriptedSupplierAgent:
    """Tiny stand-in for an Agents SDK Agent with one bound economic tool."""

    name: str
    tools: list[X402FetchTool]
    output_type: type[SupplierResearchOutput]
    instructions: str


def build_supplier_research_agent(
    application: CommerceApplication,
    *,
    request_id: str,
    idempotency_key: str,
    approval: ApprovalGrant | None,
    recorder: PurchaseResultRecorder,
    now: datetime | None = None,
) -> ScriptedSupplierAgent:
    """Create a fresh agent whose only economic tool is application-bound."""

    tool = build_x402_fetch_tool(
        application,
        request_id=request_id,
        idempotency_key=idempotency_key,
        approval=approval,
        on_purchase=recorder.record,
        now=now,
    )
    return ScriptedSupplierAgent(
        name="Synthetic supplier research agent",
        tools=[tool],
        output_type=SupplierResearchOutput,
        instructions=(
            "Use x402_fetch exactly once for the requested paid resource. "
            "The application—not you—owns merchant policy, budgets, human "
            "approval, payment execution, receipts, and audit state. Copy "
            "only facts returned by the tool. Never claim success after a "
            "denial, and never invent a report or receipt."
        ),
    )


def validate_supplier_research_output(
    output: SupplierResearchOutput,
    recorder: PurchaseResultRecorder,
) -> PurchaseResult:
    """Fail closed unless one tool purchase supports every returned field."""

    if len(recorder.results) != 1:
        raise AgentResultInvalid(
            "purchase_count_invalid",
            "A valid agent result requires exactly one completed purchase.",
        )

    purchase = recorder.results[0]
    expected = {
        "status": purchase.status,
        "report_id": purchase.report.report_id,
        "supplier": purchase.report.supplier,
        "signals": purchase.report.signals,
        "disclaimer": purchase.report.disclaimer,
        "receipt_id": purchase.receipt.receipt_id,
        "amount": str(purchase.receipt.amount),
        "currency": purchase.receipt.currency,
        "requires_human_approval": (purchase.authorization.requires_human_approval),
    }
    actual = output.model_dump()
    mismatches = sorted(
        field_name
        for field_name, expected_value in expected.items()
        if actual[field_name] != expected_value
    )
    if mismatches:
        raise AgentResultInvalid(
            "agent_output_mismatch",
            "Agent output did not match application evidence for: "
            + ", ".join(mismatches),
        )
    return purchase


def run_supplier_research(
    application: CommerceApplication,
    *,
    request_id: str,
    idempotency_key: str,
    approval: ApprovalGrant | None,
    resource_url: str = DEFAULT_RESOURCE_URL,
    purpose: str = DEFAULT_PURPOSE,
    now: datetime | None = None,
) -> SupplierResearchRun:
    """Run a deterministic one-tool loop and validate against app evidence.

    This replaces the OpenAI Agents SDK + scripted Model path from the
    upstream cookbook so Omnipay learners need only pydantic + httpx + pytest.
    """

    recorder = PurchaseResultRecorder()
    agent = build_supplier_research_agent(
        application,
        request_id=request_id,
        idempotency_key=idempotency_key,
        approval=approval,
        recorder=recorder,
        now=now,
    )
    tool = agent.tools[0]
    raw = tool(resource_url, purpose)
    evidence = json.loads(raw)
    if evidence.get("status") != "completed":
        raise AgentResultInvalid(
            "tool_denied",
            "The scripted agent received a denial instead of purchase evidence.",
        )
    report = evidence["report"]
    output = SupplierResearchOutput(
        status=evidence["status"],
        report_id=report["report_id"],
        supplier=report["supplier"],
        signals=tuple(report["signals"]),
        disclaimer=report["disclaimer"],
        receipt_id=evidence["receipt_id"],
        amount=str(evidence["amount"]),
        currency=evidence["currency"],
        requires_human_approval=evidence["requires_human_approval"],
    )
    purchase = validate_supplier_research_output(output, recorder)
    return SupplierResearchRun(output=output, purchase=purchase)
