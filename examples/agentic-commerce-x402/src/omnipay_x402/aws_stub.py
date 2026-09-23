"""Permanent stubs for live AgentCore / AWS payment paths.

Live gates are intentionally omitted from this Omnipay adaptation. Callers
receive SKIPPED / NOT_READY without any network I/O or credential use.
"""

from __future__ import annotations

from typing import Any, Literal


def live_agentcore_status() -> dict[str, Any]:
    """Report that the connected AgentCore Payments path is out of scope."""

    return {
        "status": "SKIPPED",
        "reason": "NOT_READY",
        "provider": "agentcore_payments",
        "value_transferred": False,
        "network_calls": False,
        "message": (
            "Live Amazon Bedrock AgentCore Payments is intentionally omitted "
            "from the Omnipay local simulation. Use LocalPaymentProcessor only."
        ),
    }


def create_live_payment_session(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    """Refuse any attempt to open a live payment session."""

    return live_agentcore_status()


def authorize_live_payment(*_args: Any, **_kwargs: Any) -> dict[str, Literal[False] | str]:
    """Refuse any attempt to authorize a live payment."""

    status = live_agentcore_status()
    return {
        "ok": False,
        "status": status["status"],
        "reason": status["reason"],
        "value_transferred": False,
    }
