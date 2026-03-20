"""
tools/deal_scorer.py
────────────────────
Deal qualification and risk scoring engine.

Takes free-text deal notes (from CRM, call summaries, email threads) and
extracts BANT (Budget, Authority, Need, Timeline) signals using regex and
keyword matching — no LLM required.  This makes it fast, deterministic,
and fully offline.

Outputs:
  • Qualification score (1-100) with BANT breakdown
  • Risk signals with severity levels
  • Recommended next actions based on gaps

The scoring model uses MEDDIC-inspired weighting:
  - Budget signals:    25 points max
  - Authority signals: 25 points max
  - Need signals:      25 points max
  - Timeline signals:  25 points max
  - Risk deductions:   up to -30 points

Usage (standalone):
    python -m tools.deal_scorer --notes "Met with VP Marketing at Snap..."
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Data model — structured qualification output with scoring breakdown.
# ---------------------------------------------------------------------------

@dataclass
class RiskSignal:
    """A single risk flag identified in the deal notes."""
    signal: str           # Human-readable description of the risk
    severity: str         # "low", "medium", "high", "critical"
    category: str         # Which BANT dimension or meta-category
    recommendation: str   # Suggested action to mitigate the risk


@dataclass
class BANTBreakdown:
    """Score breakdown across the four BANT dimensions."""
    budget_score: int          # 0-25
    budget_signals: List[str]  # Evidence found in notes
    authority_score: int       # 0-25
    authority_signals: List[str]
    need_score: int            # 0-25
    need_signals: List[str]
    timeline_score: int        # 0-25
    timeline_signals: List[str]


@dataclass
class DealScore:
    """Complete deal qualification assessment."""
    raw_score: int               # Pre-deduction score (0-100)
    risk_deduction: int          # Points deducted for risk signals
    final_score: int             # Final score after deductions (0-100)
    grade: str                   # Letter grade: A, B, C, D, F
    bant: BANTBreakdown          # Detailed BANT breakdown
    risks: List[RiskSignal]      # Identified risk signals
    next_actions: List[str]      # Recommended next steps
    qualification_stage: str     # "Qualified", "Needs Work", "Unqualified"

    def to_dict(self) -> Dict:
        """Serialize to a plain dictionary for JSON output."""
        return asdict(self)

    def to_markdown(self) -> str:
        """Render as a human-readable Markdown document."""
        # Build risk table rows from the risk signals list
        risk_rows = "\n".join(
            f"| {r.severity.upper()} | {r.category} | {r.signal} | {r.recommendation} |"
            for r in self.risks
        ) if self.risks else "| — | — | No critical risks identified | — |"

        # Build next actions as a numbered list for clarity
        actions = "\n".join(f"{i+1}. {a}" for i, a in enumerate(self.next_actions))

        # Build signal evidence lists for each BANT dimension
        budget_evidence = "\n".join(f"  - {s}" for s in self.bant.budget_signals) or "  - No signals detected"
        authority_evidence = "\n".join(f"  - {s}" for s in self.bant.authority_signals) or "  - No signals detected"
        need_evidence = "\n".join(f"  - {s}" for s in self.bant.need_signals) or "  - No signals detected"
        timeline_evidence = "\n".join(f"  - {s}" for s in self.bant.timeline_signals) or "  - No signals detected"

        return textwrap.dedent(f"""\
        # Deal Qualification Score

        ## Overall: {self.final_score}/100 ({self.grade}) — {self.qualification_stage}

        | Dimension | Score | Max |
        |-----------|-------|-----|
        | Budget | {self.bant.budget_score} | 25 |
        | Authority | {self.bant.authority_score} | 25 |
        | Need | {self.bant.need_score} | 25 |
        | Timeline | {self.bant.timeline_score} | 25 |
        | **Subtotal** | **{self.raw_score}** | **100** |
        | Risk Deduction | -{self.risk_deduction} | |
        | **Final Score** | **{self.final_score}** | **100** |

        ## BANT Signal Evidence

        **Budget** ({self.bant.budget_score}/25):
        {budget_evidence}

        **Authority** ({self.bant.authority_score}/25):
        {authority_evidence}

        **Need** ({self.bant.need_score}/25):
        {need_evidence}

        **Timeline** ({self.bant.timeline_score}/25):
        {timeline_evidence}

        ## Risk Signals

        | Severity | Category | Signal | Action |
        |----------|----------|--------|--------|
        {risk_rows}

        ## Recommended Next Actions
        {actions}
        """)


# ---------------------------------------------------------------------------
# Signal detection patterns — regex and keyword matchers for each BANT
# dimension.  Each pattern has a weight (how many points it contributes)
# and a human-readable label for the evidence list.
# ---------------------------------------------------------------------------

# Type alias for signal patterns: (compiled regex, points, evidence label)
SignalPattern = Tuple[re.Pattern, int, str]

def _compile_patterns(raw: List[Tuple[str, int, str]]) -> List[SignalPattern]:
    """Compile regex patterns with case-insensitive flag for performance."""
    return [(re.compile(p, re.IGNORECASE), pts, label) for p, pts, label in raw]

# ── Budget signal patterns ──
# These detect mentions of budgets, pricing discussions, funding, and
# financial approval — all indicators that money is available.
BUDGET_PATTERNS = _compile_patterns([
    (r"\$[\d,]+[KkMmBb]?", 8, "Specific dollar amount mentioned"),
    (r"\b(budget|funding|allocated|appropriated)\b", 6, "Budget terminology used"),
    (r"\b(approved|signed.?off|green.?light)\b.*\b(budget|spend|investment)\b", 10, "Budget approval language"),
    (r"\b(budget|spend)\b.*\b(approved|signed|confirmed)\b", 10, "Budget confirmed"),
    (r"\b(pricing|proposal|quote|RFP|RFQ)\b", 5, "Pricing/proposal discussion"),
    (r"\b(procurement|purchasing|finance team)\b", 5, "Procurement involved"),
    (r"\b(no budget|budget.?constrain|budget.?freeze|cost.?cut)\b", 3, "Budget constraints mentioned (negative signal)"),
    (r"\b(fiscal year|FY\d{2,4}|annual plan)\b", 4, "Fiscal planning reference"),
])

# ── Authority signal patterns ──
# These detect mentions of decision-makers, org hierarchy, and buying
# committee dynamics — indicators that the right people are involved.
AUTHORITY_PATTERNS = _compile_patterns([
    (r"\b(CEO|CTO|CRO|CMO|CFO|COO|C-suite|chief)\b", 8, "C-level contact identified"),
    (r"\b(VP|vice president|SVP|EVP)\b", 7, "VP-level contact identified"),
    (r"\b(director|head of|general manager)\b", 6, "Director-level contact"),
    (r"\b(decision.?maker|final.?say|ultimate.?authority|signs? the)\b", 10, "Decision-maker identified"),
    (r"\b(champion|internal sponsor|advocate)\b", 8, "Internal champion identified"),
    (r"\b(buying committee|stakeholder|influencer)\b", 5, "Buying committee awareness"),
    (r"\b(no access|gatekeeper|blocked|can't reach)\b", 3, "Access issues (negative signal)"),
    (r"\b(referred|introduced|connected us)\b", 5, "Referral or introduction made"),
])

# ── Need signal patterns ──
# These detect mentions of pain points, requirements, use cases, and
# business problems — indicators of genuine need for a solution.
NEED_PATTERNS = _compile_patterns([
    (r"\b(pain point|challenge|struggle|problem|issue|bottleneck)\b", 7, "Pain point articulated"),
    (r"\b(need|require|must have|essential|critical)\b", 5, "Explicit need stated"),
    (r"\b(use case|workflow|process|initiative)\b", 5, "Specific use case discussed"),
    (r"\b(ROI|return on investment|business case|cost.?sav|time.?sav)\b", 8, "ROI/business case discussed"),
    (r"\b(demo|pilot|POC|proof of concept|trial)\b", 7, "Demo or pilot requested"),
    (r"\b(evaluate|comparison|short.?list|vendor)\b", 6, "Active evaluation underway"),
    (r"\b(nice.?to.?have|not urgent|low priority|someday)\b", 3, "Low urgency (negative signal)"),
    (r"\b(impressed|excited|enthusiastic|love[ds]?)\b", 5, "Positive sentiment expressed"),
])

# ── Timeline signal patterns ──
# These detect mentions of deadlines, launch dates, quarters, and
# urgency — indicators that there's a real timeline driving the deal.
TIMELINE_PATTERNS = _compile_patterns([
    (r"\b(Q[1-4]|quarter [1-4])\b", 7, "Specific quarter referenced"),
    (r"\b(by (January|February|March|April|May|June|July|August|September|October|November|December))\b", 8, "Target month specified"),
    (r"\b(deadline|due date|launch date|go.?live)\b", 8, "Deadline or launch date mentioned"),
    (r"\b(this (week|month|quarter)|next (week|month|quarter))\b", 7, "Near-term timeline"),
    (r"\b(ASAP|urgent|immediate|rush|accelerat)\b", 8, "Urgency language"),
    (r"\b(roadmap|planning|scoping)\b", 4, "Planning phase"),
    (r"\b(no rush|no timeline|whenever|TBD|to be determined)\b", 3, "No timeline (negative signal)"),
    (r"\b(stalled|delayed|pushed|postponed|on hold)\b", 3, "Timeline stalled (negative signal)"),
    (r"\b(20\d{2})\b", 3, "Specific year referenced"),
])

# ── Risk signal patterns ──
# These detect red flags that warrant deductions from the overall score.
# Each has a severity and point deduction value.
RISK_PATTERNS: List[Tuple[re.Pattern, int, str, str, str]] = [
    (re.compile(r"\b(stalled|stuck|no progress|gone dark|ghosted|unresponsive)\b", re.IGNORECASE),
     8, "Deal momentum has stalled", "high", "Schedule a re-engagement call with a new value proposition or relevant trigger event"),
    (re.compile(r"\b(no champion|no sponsor|no internal)\b", re.IGNORECASE),
     10, "No internal champion identified", "critical", "Identify and cultivate an internal advocate before investing more resources"),
    (re.compile(r"\b(budget unclear|no budget|budget.?freeze|cost.?cut)\b", re.IGNORECASE),
     8, "Budget uncertainty or constraints", "high", "Quantify ROI and build a business case to help champion secure funding"),
    (re.compile(r"\b(competitor|alternative|also (looking|evaluating|considering))\b", re.IGNORECASE),
     5, "Active competitive evaluation", "medium", "Sharpen differentiation and prepare battle card for competitive positioning"),
    (re.compile(r"\b(legal|compliance|security review|infosec)\b", re.IGNORECASE),
     3, "Legal or compliance review required", "low", "Proactively provide security documentation and compliance certifications"),
    (re.compile(r"\b(reorg|restructur|layoff|hiring freeze)\b", re.IGNORECASE),
     7, "Organizational instability", "high", "Validate that your sponsor and budget are still intact post-restructuring"),
    (re.compile(r"\b(pushed|delayed|postponed|on hold|back burner)\b", re.IGNORECASE),
     6, "Timeline has been pushed or deal put on hold", "medium", "Set a specific follow-up date and offer a lower-commitment next step"),
    (re.compile(r"\b(too expensive|over budget|price concern|sticker shock)\b", re.IGNORECASE),
     7, "Pricing objection raised", "high", "Reframe conversation around value and ROI; explore flexible pricing or phased rollout"),
]


# ---------------------------------------------------------------------------
# Core scoring function — entry point for CLI, Streamlit, and programmatic use.
# ---------------------------------------------------------------------------

def score_deal(notes: str) -> DealScore:
    """
    Analyze deal notes and produce a qualification score with BANT breakdown.

    This function is pure Python — no LLM, no API key, no external
    dependencies.  It uses pattern matching and keyword extraction to
    identify qualification signals and risk factors in free-text notes.

    Parameters
    ----------
    notes : str
        Free-text deal notes (CRM entries, call summaries, email excerpts).

    Returns
    -------
    DealScore
        Complete qualification assessment with BANT breakdown, risk signals,
        and recommended next actions.
    """
    # ── Score each BANT dimension by scanning for matching patterns ──
    budget_score, budget_signals = _score_dimension(notes, BUDGET_PATTERNS, max_score=25)
    authority_score, authority_signals = _score_dimension(notes, AUTHORITY_PATTERNS, max_score=25)
    need_score, need_signals = _score_dimension(notes, NEED_PATTERNS, max_score=25)
    timeline_score, timeline_signals = _score_dimension(notes, TIMELINE_PATTERNS, max_score=25)

    # Build the BANT breakdown dataclass
    bant = BANTBreakdown(
        budget_score=budget_score, budget_signals=budget_signals,
        authority_score=authority_score, authority_signals=authority_signals,
        need_score=need_score, need_signals=need_signals,
        timeline_score=timeline_score, timeline_signals=timeline_signals,
    )

    # ── Calculate raw score before risk deductions ──
    raw_score = budget_score + authority_score + need_score + timeline_score

    # ── Detect risk signals and calculate deductions ──
    risks: List[RiskSignal] = []
    risk_deduction = 0
    for pattern, deduction, signal_text, severity, recommendation in RISK_PATTERNS:
        if pattern.search(notes):
            risks.append(RiskSignal(
                signal=signal_text,
                severity=severity,
                category=_categorize_risk(signal_text),
                recommendation=recommendation,
            ))
            risk_deduction += deduction

    # Cap risk deduction at 30 points so a deal with signals isn't zeroed out
    risk_deduction = min(risk_deduction, 30)

    # ── Compute final score and assign a letter grade ──
    final_score = max(0, raw_score - risk_deduction)
    grade = _assign_grade(final_score)
    stage = _assign_stage(final_score)

    # ── Generate recommended next actions based on the weakest dimensions ──
    next_actions = _generate_next_actions(bant, risks)

    return DealScore(
        raw_score=raw_score,
        risk_deduction=risk_deduction,
        final_score=final_score,
        grade=grade,
        bant=bant,
        risks=risks,
        next_actions=next_actions,
        qualification_stage=stage,
    )


def _score_dimension(
    notes: str,
    patterns: List[SignalPattern],
    max_score: int,
) -> Tuple[int, List[str]]:
    """
    Score a single BANT dimension by checking each pattern against the notes.
    Returns the capped score and a list of evidence labels for matched patterns.
    """
    total = 0
    signals: List[str] = []

    for pattern, points, label in patterns:
        # Find all matches for this pattern in the notes
        matches = pattern.findall(notes)
        if matches:
            total += points
            # Include the matched text for context in evidence list
            match_preview = matches[0] if isinstance(matches[0], str) else str(matches[0])
            signals.append(f"{label} (matched: '{match_preview}')")

    # Cap the score at the dimension maximum to prevent one dimension
    # from overwhelming the others
    return min(total, max_score), signals


def _assign_grade(score: int) -> str:
    """Map a numeric score to a letter grade for quick assessment."""
    if score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 55:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


def _assign_stage(score: int) -> str:
    """Map a numeric score to a qualification stage label."""
    if score >= 70:
        return "Qualified — ready for proposal"
    elif score >= 45:
        return "Needs Work — gaps in qualification"
    else:
        return "Unqualified — significant gaps remain"


def _categorize_risk(signal_text: str) -> str:
    """Assign a BANT category to a risk signal for reporting purposes."""
    # Map risk signals to their most relevant BANT dimension
    text_lower = signal_text.lower()
    if "budget" in text_lower or "pricing" in text_lower:
        return "Budget"
    elif "champion" in text_lower or "sponsor" in text_lower:
        return "Authority"
    elif "competitor" in text_lower:
        return "Need"
    elif "stall" in text_lower or "timeline" in text_lower or "hold" in text_lower or "push" in text_lower:
        return "Timeline"
    elif "legal" in text_lower or "compliance" in text_lower:
        return "Process"
    elif "reorg" in text_lower or "restructur" in text_lower:
        return "Authority"
    else:
        return "General"


def _generate_next_actions(bant: BANTBreakdown, risks: List[RiskSignal]) -> List[str]:
    """
    Generate prioritized next actions based on the weakest BANT dimensions
    and the most critical risk signals.
    """
    actions: List[str] = []

    # ── Address the weakest BANT dimensions first ──
    dimension_scores = [
        ("Budget", bant.budget_score, 25),
        ("Authority", bant.authority_score, 25),
        ("Need", bant.need_score, 25),
        ("Timeline", bant.timeline_score, 25),
    ]

    # Sort by score ascending to prioritize the weakest dimensions
    dimension_scores.sort(key=lambda x: x[1])

    # Generate specific actions for each weak dimension (below 60% of max)
    for name, score, max_pts in dimension_scores:
        threshold = max_pts * 0.6  # 60% threshold for "weak"
        if score < threshold:
            if name == "Budget":
                actions.append(
                    "Clarify budget: Ask directly about allocated budget, fiscal year "
                    "timing, and approval process. Prepare ROI model to justify spend."
                )
            elif name == "Authority":
                actions.append(
                    "Map the buying committee: Identify the economic buyer, technical "
                    "evaluator, and internal champion. Request an org chart discussion."
                )
            elif name == "Need":
                actions.append(
                    "Deepen discovery: Schedule a pain-point workshop to quantify the "
                    "business impact of the problem. Get the prospect to articulate need."
                )
            elif name == "Timeline":
                actions.append(
                    "Establish timeline: Ask about driving events (board meetings, "
                    "product launches, contract expirations) that create natural urgency."
                )

    # ── Add risk-specific actions for critical/high severity ──
    for risk in risks:
        if risk.severity in ("critical", "high"):
            actions.append(f"[{risk.severity.upper()} RISK] {risk.recommendation}")

    # ── Always include a general best practice ──
    if not actions:
        actions.append(
            "Deal is well-qualified. Focus on advancing to proposal stage — "
            "confirm pricing expectations, timeline, and procurement process."
        )

    return actions


# ---------------------------------------------------------------------------
# Standalone execution for quick testing.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Score deal qualification from notes")
    parser.add_argument(
        "--notes",
        default=(
            "Met with VP Marketing at Snap Inc. They're interested in launching a "
            "pilot in Q3. Budget of $150K has been approved by the CMO. Main pain "
            "point is scaling personalized outreach — their team spends 3 hours per "
            "prospect on research. They're also evaluating a competitor (Outreach.io). "
            "No internal champion identified yet. Need to get in front of the "
            "Director of Sales Enablement."
        ),
        help="Free-text deal notes to analyze",
    )
    args = parser.parse_args()

    result = score_deal(args.notes)
    print(result.to_markdown())
