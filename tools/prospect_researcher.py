"""
tools/prospect_researcher.py
─────────────────────────────
AI-augmented prospect research tool.

Takes a company name and produces a structured research brief including
company overview, recent news themes, potential pain points, and a
recommended approach angle.

Supports two modes:
  • mock  (default) — returns pre-built, realistic responses so the tool
    can be demoed without any API key.
  • live  — sends a structured prompt to any OpenAI-compatible chat API
    (Claude, GPT, Gemini via proxy, local models, etc.).

Usage (standalone):
    python -m tools.prospect_researcher "Snap Inc"
"""

from __future__ import annotations

import json
import os
import textwrap
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Data model — every research brief follows this schema so downstream tools
# (outreach personalizer, battle card generator) can consume it reliably.
# ---------------------------------------------------------------------------

@dataclass
class ProspectBrief:
    """Structured research output for a single prospect company."""
    company: str
    overview: str
    industry: str
    estimated_revenue: str
    employee_count: str
    headquarters: str
    recent_news: List[str]
    pain_points: List[str]
    recommended_angles: List[str]
    key_contacts_to_target: List[str]
    competitive_landscape: str
    tech_stack_signals: List[str]

    def to_dict(self) -> Dict:
        """Serialize the brief to a plain dictionary for JSON output."""
        return asdict(self)

    def to_markdown(self) -> str:
        """Render the brief as a human-readable Markdown document."""
        # Build bullet lists from list fields for clean Markdown output
        news_bullets = "\n".join(f"- {item}" for item in self.recent_news)
        pain_bullets = "\n".join(f"- {item}" for item in self.pain_points)
        angle_bullets = "\n".join(f"- {item}" for item in self.recommended_angles)
        contact_bullets = "\n".join(f"- {item}" for item in self.key_contacts_to_target)
        tech_bullets = "\n".join(f"- {item}" for item in self.tech_stack_signals)

        return textwrap.dedent(f"""\
        # Prospect Research Brief — {self.company}

        ## Company Overview
        {self.overview}

        | Detail | Value |
        |--------|-------|
        | Industry | {self.industry} |
        | Est. Revenue | {self.estimated_revenue} |
        | Employees | {self.employee_count} |
        | HQ | {self.headquarters} |

        ## Recent News & Triggers
        {news_bullets}

        ## Potential Pain Points
        {pain_bullets}

        ## Recommended Approach Angles
        {angle_bullets}

        ## Key Contacts to Target
        {contact_bullets}

        ## Competitive Landscape
        {self.competitive_landscape}

        ## Tech Stack Signals
        {tech_bullets}
        """)


# ---------------------------------------------------------------------------
# Mock data — hand-crafted, realistic briefs for demo purposes.  Each entry
# is keyed by a lowercase company name.  When a company isn't in the map we
# generate a plausible generic brief so the demo never errors.
# ---------------------------------------------------------------------------

_MOCK_BRIEFS: Dict[str, Dict] = {
    "snap inc": {
        "company": "Snap Inc.",
        "overview": (
            "Snap Inc. is the parent company of Snapchat, a visual messaging app, "
            "and Spectacles, AR-enabled smart glasses. Founded in 2011, Snap pioneered "
            "ephemeral content and has since expanded into augmented reality, content "
            "platforms (Discover & Spotlight), and AI with My AI chatbot. The company "
            "reported $4.6B in revenue for FY2024, driven primarily by advertising."
        ),
        "industry": "Social Media / Augmented Reality / Digital Advertising",
        "estimated_revenue": "$4.6B (FY2024)",
        "employee_count": "~5,300",
        "headquarters": "Santa Monica, CA",
        "recent_news": [
            "Launched Snap AR Enterprise Services targeting retail and e-commerce brands",
            "Expanded Snapchat+ subscription to 12M+ paying users, signaling diversification beyond ads",
            "Announced restructuring of sales org to focus on mid-market advertisers",
            "Partnered with Amazon for in-app AR try-on shopping experiences",
            "Invested heavily in ML-driven ad optimization (7x7 campaign architecture)",
        ],
        "pain_points": [
            "Advertiser churn in brand/awareness budgets — performance advertisers dominate spend",
            "Sales team stretched thin across SMB and enterprise without clear segmentation tooling",
            "Attribution gaps make it hard for brand advertisers to justify Snapchat spend vs. Meta/TikTok",
            "Content moderation at scale for Spotlight UGC creates legal and brand-safety exposure",
            "Retention of mid-level sales talent in competitive adtech hiring market",
        ],
        "recommended_angles": [
            "Position around helping their sales team scale personalized outreach to mid-market agencies — aligns with restructuring priority",
            "Lead with attribution/measurement narrative — Snap is actively seeking partners who solve the 'prove it works' problem for brand budgets",
            "AR commerce angle: their Amazon partnership signals appetite for tech partnerships that drive measurable conversion",
        ],
        "key_contacts_to_target": [
            "VP of Sales, Americas — owns the mid-market restructuring mandate",
            "Head of Ad Products & Measurement — decision-maker on attribution tooling",
            "Director of Revenue Operations — likely evaluating CRM and enablement stack",
            "Chief Business Officer — executive sponsor for partnership deals",
        ],
        "competitive_landscape": (
            "Snap competes for ad dollars with Meta (Instagram Reels), TikTok, YouTube Shorts, "
            "and Pinterest. In AR, Apple Vision Pro and Meta Quest are emerging threats. Snap's "
            "differentiation rests on its younger demographic (13-34), camera-first UX, and AR "
            "developer ecosystem. Weakness: lower time-spent-per-user vs. TikTok."
        ),
        "tech_stack_signals": [
            "Google Cloud Platform (primary cloud provider, multi-year deal)",
            "Salesforce CRM (referenced in job postings for Rev Ops roles)",
            "Tableau for BI/reporting (Salesforce ecosystem)",
            "Internal ML platform for ad ranking and content recommendation",
        ],
    },
    "hubspot": {
        "company": "HubSpot, Inc.",
        "overview": (
            "HubSpot is a leading CRM and inbound marketing platform serving 200K+ "
            "customers globally. The company offers Marketing Hub, Sales Hub, Service Hub, "
            "CMS Hub, and Operations Hub. Known for pioneering 'inbound marketing,' HubSpot "
            "has expanded into AI with Breeze Copilot and Breeze Agents, embedding generative "
            "AI across its product suite."
        ),
        "industry": "SaaS / CRM / Marketing Technology",
        "estimated_revenue": "$2.6B (FY2024)",
        "employee_count": "~7,700",
        "headquarters": "Cambridge, MA",
        "recent_news": [
            "Launched Breeze AI agents for automated prospecting and customer service",
            "Alphabet/Google acquisition talks reportedly stalled — company remains independent",
            "Expanded Commerce Hub to compete with Shopify in B2B e-commerce",
            "Announced 'Spotlight' AI features at INBOUND 2024 conference",
            "Growing enterprise push with HubSpot Enterprise tier and custom objects",
        ],
        "pain_points": [
            "Enterprise credibility gap — still perceived as SMB tool by large accounts",
            "Sales team needs to articulate AI differentiation vs. Salesforce Einstein and Microsoft Copilot",
            "Channel partner enablement is inconsistent across regions",
            "Data quality issues when migrating enterprise prospects from legacy CRMs",
            "Pricing pressure from freemium competitors (Zoho, Freshworks)",
        ],
        "recommended_angles": [
            "Help their sales team demo AI capabilities more effectively against Salesforce — enablement gap",
            "Offer content/thought leadership partnership around 'AI for revenue teams' to boost enterprise credibility",
            "Partner on channel enablement programs — they need scalable training for partner agencies",
        ],
        "key_contacts_to_target": [
            "VP of Sales, Enterprise — owns the upmarket motion",
            "Head of AI Product Marketing — needs competitive positioning support",
            "Director of Partner Programs — channel enablement budget holder",
            "CRO — strategic decisions on go-to-market investments",
        ],
        "competitive_landscape": (
            "HubSpot competes with Salesforce (enterprise CRM), Microsoft Dynamics 365, "
            "Zoho (SMB value play), and point solutions like Outreach, Gong, and Apollo.io. "
            "Strength: unified platform with low total cost of ownership. Weakness: feature depth "
            "in any single module vs. best-of-breed."
        ),
        "tech_stack_signals": [
            "AWS (primary cloud infrastructure)",
            "Internal CRM (dogfooding HubSpot platform)",
            "Snowflake for data warehousing",
            "Custom ML infrastructure for Breeze AI",
        ],
    },
}


def _build_generic_brief(company: str) -> Dict:
    """
    Generate a plausible generic brief for companies not in the mock data.
    This ensures the demo never fails regardless of the company entered.
    """
    return {
        "company": company,
        "overview": (
            f"{company} is a mid-to-large enterprise operating in a competitive market segment. "
            f"The company has been investing in digital transformation and exploring AI-driven "
            f"efficiencies across marketing, sales, and operations. Recent earnings calls reference "
            f"a focus on operational leverage and customer retention."
        ),
        "industry": "Technology / Digital Services",
        "estimated_revenue": "$500M - $2B (estimated)",
        "employee_count": "1,000 - 10,000",
        "headquarters": "United States",
        "recent_news": [
            f"{company} announced a strategic initiative around AI adoption in Q4 2025",
            f"Leadership restructuring in go-to-market org signals new growth priorities",
            f"Expanded partnerships with cloud providers for infrastructure modernization",
            f"Launched a customer advisory board to inform product roadmap",
            f"Earnings beat expectations, with management citing 'efficiency gains from automation'",
        ],
        "pain_points": [
            "Sales team productivity — reps spend too much time on research and admin vs. selling",
            "Inconsistent messaging across regions and segments leads to pipeline leakage",
            "CRM data hygiene issues make forecasting unreliable",
            "Competitive pressure forcing faster deal cycles with less margin for error",
            "Talent retention in sales org as competitors offer AI-augmented workflows",
        ],
        "recommended_angles": [
            "Lead with productivity narrative — quantify time savings from AI-augmented workflows",
            "Offer a pilot program tied to a specific segment to reduce perceived risk",
            f"Reference {company}'s own AI investments to create alignment ('we help you do internally what you're building externally')",
        ],
        "key_contacts_to_target": [
            "VP of Sales / CRO — strategic budget authority",
            "Head of Revenue Operations — evaluates enablement tooling",
            "Director of Sales Enablement — day-to-day buyer for training and content",
            "Chief Digital Officer — sponsors transformation initiatives",
        ],
        "competitive_landscape": (
            f"{company} operates in a market with 3-5 major competitors and several niche players. "
            f"Differentiation is increasingly driven by technology adoption, customer experience, "
            f"and speed-to-value. Companies that lag on AI adoption risk losing deals to more "
            f"agile competitors."
        ),
        "tech_stack_signals": [
            "Likely uses a major CRM (Salesforce, HubSpot, or Dynamics 365)",
            "Cloud infrastructure on AWS, GCP, or Azure",
            "Business intelligence tools (Tableau, Looker, or Power BI)",
            "Marketing automation (Marketo, Pardot, or HubSpot Marketing Hub)",
        ],
    }


# ---------------------------------------------------------------------------
# Core research function — entry point for CLI, Streamlit, and programmatic use.
# ---------------------------------------------------------------------------

def research_prospect(
    company: str,
    *,
    mode: str = "mock",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
) -> ProspectBrief:
    """
    Generate a structured research brief for a prospect company.

    Parameters
    ----------
    company : str
        The name of the company to research.
    mode : str
        "mock" (default) for demo-ready responses, "live" for API calls.
    api_key : str, optional
        API key for live mode. Falls back to OPENAI_API_KEY env var.
    api_base : str, optional
        Base URL for the chat completions API (supports any OpenAI-compatible
        endpoint: OpenAI, Azure, Anthropic proxy, Ollama, etc.).
    model : str, optional
        Model identifier (e.g., "gpt-4o", "claude-3-opus-20240229").

    Returns
    -------
    ProspectBrief
        A dataclass containing the full research output.
    """
    if mode == "mock":
        return _research_mock(company)
    elif mode == "live":
        return _research_live(company, api_key=api_key, api_base=api_base, model=model)
    else:
        raise ValueError(f"Unknown mode '{mode}'. Use 'mock' or 'live'.")


def _research_mock(company: str) -> ProspectBrief:
    """
    Return a mock research brief.  Looks up the company in the pre-built
    mock data; falls back to a generic but plausible brief.
    """
    # Normalize the lookup key to lowercase for case-insensitive matching
    key = company.strip().lower()
    data = _MOCK_BRIEFS.get(key, _build_generic_brief(company))
    return ProspectBrief(**data)


def _research_live(
    company: str,
    *,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
) -> ProspectBrief:
    """
    Call an OpenAI-compatible chat completions API with a structured prompt
    to generate a real research brief.  Requires the `openai` package and
    a valid API key.
    """
    # ── Resolve configuration from args or environment variables ──
    resolved_key = api_key or os.getenv("OPENAI_API_KEY", "")
    resolved_base = api_base or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-4o")

    if not resolved_key:
        raise EnvironmentError(
            "Live mode requires an API key. Set OPENAI_API_KEY or pass api_key=."
        )

    # ── Lazy import so mock mode has zero external dependencies ──
    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        raise ImportError(
            "Live mode requires the 'openai' package. Install with: pip install openai"
        )

    # ── Build the structured prompt that guides the LLM to produce JSON ──
    system_prompt = textwrap.dedent("""\
        You are a senior sales research analyst. Given a company name, produce
        a thorough prospect research brief in JSON format matching this schema:

        {
          "company": "string",
          "overview": "string (2-3 sentences)",
          "industry": "string",
          "estimated_revenue": "string",
          "employee_count": "string",
          "headquarters": "string",
          "recent_news": ["string (5 items)"],
          "pain_points": ["string (5 items)"],
          "recommended_angles": ["string (3 items)"],
          "key_contacts_to_target": ["string (4 items, role + context)"],
          "competitive_landscape": "string (2-3 sentences)",
          "tech_stack_signals": ["string (4 items)"]
        }

        Be specific, data-driven, and actionable. Reference real market dynamics.
        Return ONLY valid JSON — no markdown fences, no commentary.
    """)

    user_prompt = f"Research the company: {company}"

    # ── Make the API call ──
    client = OpenAI(api_key=resolved_key, base_url=resolved_base)
    response = client.chat.completions.create(
        model=resolved_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,  # Lower temperature for factual, consistent output
        max_tokens=2000,
    )

    # ── Parse the JSON response into our dataclass ──
    raw = response.choices[0].message.content.strip()
    data = json.loads(raw)
    return ProspectBrief(**data)


# ---------------------------------------------------------------------------
# Standalone execution — allows running the tool directly for quick testing.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    company_name = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Snap Inc"
    brief = research_prospect(company_name)
    print(brief.to_markdown())
