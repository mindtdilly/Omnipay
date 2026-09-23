"""Local-only x402 agentic commerce simulation for Omnipay / ProcureNet docs.

Adapted from the OpenAI Cookbook example
``controlled_agentic_commerce_with_agentcore_payments``. This package never
moves real funds, never calls AWS/AgentCore, and uses only synthetic proofs.
"""

from .agent import SupplierResearchOutput, run_supplier_research
from .application import CommerceApplication
from .aws_stub import live_agentcore_status
from .merchant import SyntheticMerchant
from .models import (
    ApprovalGrant,
    CommercePolicy,
    PurchaseRequest,
    PurchaseResult,
)
from .payments import LocalPaymentProcessor
from .policy import PolicyEngine

VALUE_TRANSFERRED = False

__all__ = [
    "ApprovalGrant",
    "CommerceApplication",
    "CommercePolicy",
    "LocalPaymentProcessor",
    "PolicyEngine",
    "PurchaseRequest",
    "PurchaseResult",
    "SupplierResearchOutput",
    "SyntheticMerchant",
    "VALUE_TRANSFERRED",
    "live_agentcore_status",
    "run_supplier_research",
]
