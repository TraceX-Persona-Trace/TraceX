"""
Intelligence schemas for Chunk 7.

Defines the structured output of the investigation intelligence service.

All fields are derived from real Evidence, reconstruction attributes, and
matching results. No AI inference, no synthetic confidence, no external data.

The architecture is designed so that a future AI/LLM provider can add
narrative summaries or enhanced scoring by consuming IntelligenceResult
without modifying the signal-generation layer.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


# ---- Signal types ----
# Each string constant is the canonical type identifier for a signal.
# New signal types can be added here in future chunks.

SIGNAL_CROSS_INVESTIGATION_MATCH = "cross_investigation_match"
SIGNAL_REPEATED_ATTRIBUTE        = "repeated_attribute"
SIGNAL_HIGH_CONFIDENCE_EVIDENCE  = "high_confidence_evidence"
SIGNAL_NO_MATCHABLE_ATTRIBUTES   = "no_matchable_attributes"
SIGNAL_NO_CROSS_INVESTIGATION    = "no_cross_investigation_match"
SIGNAL_NO_EVIDENCE               = "no_evidence"

# ---- Severity levels ----
SEVERITY_INFO   = "info"
SEVERITY_LOW    = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH   = "high"


class IntelligenceSignal(BaseModel):
    """
    A single structured intelligence observation derived from real evidence
    and/or matching results.

    Every signal is explainable and traceable:
        evidence_ids       → specific Evidence rows that produced this signal
        investigation_ids  → investigations involved (may include others)
        match_rule         → the Chunk 6 match rule if this came from matching

    No synthetic confidence is generated. When a signal includes a
    confidence value, it is taken directly from an existing Evidence row.
    """
    signal_type: str                      # one of the SIGNAL_* constants above
    title: str                            # short human-readable label
    explanation: str                      # full explanation of why this signal was raised
    severity: str                         # one of the SEVERITY_* constants above
    evidence_ids: List[int]               # traceability: which Evidence rows
    investigation_ids: List[int]          # traceability: which Investigations
    match_rule: Optional[str] = None      # set when signal came from matching
    attribute_value: Optional[str] = None # the normalised value involved, if applicable
    evidence_type: Optional[str] = None   # evidence_type involved, if applicable
    source_confidence: Optional[float] = None  # real Evidence.confidence, not synthetic


class IntelligenceResult(BaseModel):
    """
    Full intelligence result for one investigation.

    The result is computed deterministically from existing data every time
    the endpoint is called — it is not persisted.

    `provider` identifies what generated the intelligence. Currently always
    "deterministic" (Chunk 7 baseline). When a future AI/LLM provider is
    configured, it will add its own signals and change provider to its name,
    while keeping all deterministic signals intact.
    """
    investigation_id: int
    signals: List[IntelligenceSignal]
    summary: str                  # one-sentence human-readable summary
    total_evidence: int           # how many evidence rows were analysed
    total_signals: int            # total number of signals raised
    provider: str                 # "deterministic" | future: "openai", "anthropic", etc.
    generated_at: datetime
