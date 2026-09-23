"""Scripted learning loop without OpenAI Agents SDK or network inference.

Upstream cookbook used ``ScriptedCommerceLearningModel`` implementing the
Agents SDK ``Model`` interface. Omnipay keeps the same teaching intent via
``run_supplier_research`` in ``agent.py``.
"""

from __future__ import annotations

from .agent import run_supplier_research

__all__ = ["run_supplier_research"]
