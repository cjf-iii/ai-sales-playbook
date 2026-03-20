"""
tools/battle_card_generator.py
──────────────────────────────
Competitive battle card generation tool.

Takes your product context and a competitor name, then produces a structured
battle card with strengths, weaknesses, objection handling, and
differentiators.  Designed for use in deal rooms, sales kickoffs, and
competitive win/loss reviews.

Supports mock mode (default) and live mode (OpenAI-compatible API).

Usage (standalone):
    python -m tools.battle_card_generator --competitor "Google Ads"
"""

from __future__ import annotations

import json
import os
import textwrap
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Data model — a battle card follows a standard competitive intelligence
# structure used by enterprise sales teams worldwide.
# ---------------------------------------------------------------------------

@dataclass
class ObjectionResponse:
    """A common objection raised by prospects and the recommended response."""
    objection: str       # What the prospect says
    response: str        # How to counter it
    proof_point: str     # Evidence or case study to back the response


@dataclass
class BattleCard:
    """Complete competitive battle card for use in deal rooms and training."""
    your_product: str
    competitor: str
    competitor_overview: str
    # ── Competitive analysis ──
    competitor_strengths: List[str]
    competitor_weaknesses: List[str]
    your_differentiators: List[str]
    # ── Tactical guidance ──
    when_you_win: List[str]          # Scenarios where you typically win
    when_you_lose: List[str]         # Scenarios where the competitor wins
    objection_handling: List[ObjectionResponse]
    # ── Positioning ──
    elevator_pitch_vs_competitor: str
    trap_questions: List[str]        # Questions to ask that expose competitor weaknesses
    landmine_questions: List[str]    # Questions competitors ask to expose YOUR weaknesses
    landmine_responses: List[str]    # How to handle landmine questions

    def to_dict(self) -> Dict:
        """Serialize to a plain dictionary for JSON output."""
        return asdict(self)

    def to_markdown(self) -> str:
        """Render as a human-readable Markdown document."""
        # Build formatted sections from list fields
        strengths = "\n".join(f"- {s}" for s in self.competitor_strengths)
        weaknesses = "\n".join(f"- {w}" for w in self.competitor_weaknesses)
        diffs = "\n".join(f"- {d}" for d in self.your_differentiators)
        wins = "\n".join(f"- {w}" for w in self.when_you_win)
        losses = "\n".join(f"- {l}" for l in self.when_you_lose)
        traps = "\n".join(f"- \"{q}\"" for q in self.trap_questions)
        landmines = "\n".join(f"- \"{q}\"" for q in self.landmine_questions)
        landmine_resp = "\n".join(f"- {r}" for r in self.landmine_responses)

        # Build objection handling table
        objection_rows = "\n".join(
            f"| \"{o.objection}\" | {o.response} | {o.proof_point} |"
            for o in self.objection_handling
        )

        return textwrap.dedent(f"""\
        # Battle Card: {self.your_product} vs. {self.competitor}

        ## Competitor Overview
        {self.competitor_overview}

        ## Competitor Strengths
        {strengths}

        ## Competitor Weaknesses
        {weaknesses}

        ## Our Differentiators
        {diffs}

        ## When We Win
        {wins}

        ## When We Lose
        {losses}

        ## Elevator Pitch (vs. {self.competitor})
        > {self.elevator_pitch_vs_competitor}

        ## Objection Handling

        | Objection | Response | Proof Point |
        |-----------|----------|-------------|
        {objection_rows}

        ## Trap Questions (Expose Their Weaknesses)
        {traps}

        ## Landmine Questions (They'll Ask About Us)
        {landmines}

        ### How to Respond
        {landmine_resp}
        """)


# ---------------------------------------------------------------------------
# Default product context — represents a fictional "AdTech Solutions"
# product for demo purposes.  In production, this would be configured
# per-organization.
# ---------------------------------------------------------------------------

DEFAULT_PRODUCT = {
    "name": "AdTech Solutions AI Platform",
    "category": "AI-Powered Sales Enablement",
    "key_capabilities": [
        "AI-augmented prospect research",
        "Personalized outreach at scale",
        "Deal qualification scoring",
        "Competitive intelligence automation",
        "CRM integration (Salesforce, HubSpot)",
    ],
    "ideal_customer": "Mid-market to enterprise B2B sales teams (50-500 reps)",
}


# ---------------------------------------------------------------------------
# Mock battle card data — realistic, detailed cards for common competitors
# that demonstrate the tool's output quality.
# ---------------------------------------------------------------------------

_MOCK_CARDS: Dict[str, Dict] = {
    "google ads": {
        "competitor": "Google Ads",
        "competitor_overview": (
            "Google Ads is the dominant digital advertising platform, offering "
            "search, display, video (YouTube), and shopping ad formats. With $238B "
            "in ad revenue (2023), Google commands ~28% of global digital ad spend. "
            "Their strength is intent-based targeting and massive reach. Recent "
            "investments in Performance Max (AI-driven campaign automation) and "
            "generative AI for ad creative signal a push toward full-funnel automation."
        ),
        "competitor_strengths": [
            "Unmatched reach — access to 90%+ of internet users globally",
            "Intent-based targeting through search is uniquely powerful for bottom-funnel",
            "Performance Max uses Google's AI to optimize across all surfaces automatically",
            "Deep first-party data from Gmail, Chrome, Android, YouTube, Maps",
            "Self-serve platform with low barrier to entry for SMB advertisers",
        ],
        "competitor_weaknesses": [
            "Brand safety concerns on YouTube and Display Network remain persistent",
            "Attribution is a black box — limited transparency into how conversions are counted",
            "Rising CPCs are pricing out mid-market advertisers in competitive verticals",
            "Customer support is notoriously poor — SMBs get bot-driven support only",
            "Privacy changes (cookie deprecation, ATT) are eroding targeting precision",
            "Creative tools are still basic compared to platform-native social ads",
        ],
        "your_differentiators": [
            "We help sales teams sell AGAINST Google Ads by arming them with competitive data",
            "Our AI research tools surface Google's specific weaknesses for each prospect's vertical",
            "Personalized outreach that positions alternatives as complementary, not competitive",
            "Deal scoring identifies which prospects are most likely to diversify beyond Google",
            "We enable the conversation Google can't have: transparent, consultative, ROI-focused",
        ],
        "when_you_win": [
            "Prospect has been burned by Google's attribution opacity and wants transparent reporting",
            "Mid-market advertiser is priced out of competitive Google verticals and looking for alternatives",
            "Brand safety incident on YouTube has leadership questioning Google-heavy media mix",
            "Prospect values consultative sales relationship over self-serve platform",
        ],
        "when_you_lose": [
            "Prospect is a direct-response advertiser with strong Google ROAS and no reason to change",
            "Google offers aggressive co-marketing dollars or credits to lock in the account",
            "Prospect's agency is a Google Premier Partner with financial incentives to stay",
            "Scale requirements exceed what alternative platforms can deliver",
        ],
        "objection_handling": [
            {
                "objection": "Google Ads drives most of our conversions — why would we change?",
                "response": "We're not suggesting you stop Google Ads. We help you diversify so you're not over-indexed on a single channel. Our clients who diversify see 20-30% lower blended CPA.",
                "proof_point": "Case study: MediaCorp reduced Google dependency from 70% to 45% of spend while improving overall ROAS by 22%.",
            },
            {
                "objection": "Performance Max automates everything — we don't need additional tools.",
                "response": "Performance Max optimizes within Google's ecosystem, but it can't tell you where Google is overspending. Our platform gives you the cross-channel view Google can't provide.",
                "proof_point": "Analysis of 50 mid-market accounts showed PMax over-allocated to low-value display inventory in 67% of cases.",
            },
            {
                "objection": "Google's reach is unmatched — nothing else compares.",
                "response": "Reach without precision is waste. As CPCs rise and cookies disappear, the question isn't reach — it's efficiency. We help you find the 30% of spend that's not working.",
                "proof_point": "Average client identifies $45K/quarter in wasted Google spend within the first 30 days of using our platform.",
            },
        ],
        "elevator_pitch_vs_competitor": (
            "Google Ads is a powerful machine, but it's a black box that optimizes "
            "for Google's interests, not yours. We give your sales team the intelligence "
            "to have honest conversations about media mix diversification — backed by "
            "data, not opinions. The result: prospects trust you more, deals close faster, "
            "and accounts retain longer because they're not over-indexed on a single channel."
        ),
        "trap_questions": [
            "How do you measure incrementality — do you know which conversions would have happened anyway?",
            "What percentage of your Display Network placements are on sites your brand would approve of?",
            "How has your CPC trended over the last 8 quarters, and what's your plan when it doubles again?",
            "Can you see exactly where Performance Max allocated your budget, or is it a black box?",
        ],
        "landmine_questions": [
            "Can you match Google's reach and scale?",
            "Do you have access to search intent data?",
            "What's your self-serve platform experience like?",
        ],
        "landmine_responses": [
            "We don't compete on raw reach — we compete on efficiency. Our clients don't need to reach everyone; they need to reach the right people with the right message.",
            "We complement search intent with behavioral and contextual signals that Google can't access. Together with search, this creates a more complete picture.",
            "We're a managed platform by design — because the 'set it and forget it' approach of self-serve is exactly what leads to wasted spend. Our clients value the strategic guidance.",
        ],
    },
    "outreach.io": {
        "competitor": "Outreach.io",
        "competitor_overview": (
            "Outreach is a leading sales execution platform focused on email sequencing, "
            "call automation, and pipeline management. Used by 5,500+ companies including "
            "Adobe, Okta, and Snowflake. Outreach competes primarily on workflow automation "
            "for SDR/BDR teams and has expanded into revenue intelligence with Outreach Kaia "
            "(conversation intelligence) and deal health scoring."
        ),
        "competitor_strengths": [
            "Market leader in sales engagement — strong brand recognition and trust",
            "Deep email sequencing with A/B testing, throttling, and deliverability optimization",
            "Kaia conversation intelligence adds real-time call coaching and transcription",
            "Enterprise-grade Salesforce integration with bi-directional sync",
            "Large ecosystem of integrations (200+) and active partner community",
        ],
        "competitor_weaknesses": [
            "Pricing is aggressive — $100-150/user/month puts it out of reach for many mid-market teams",
            "AI features (Smart Email Assist) produce generic output that reps still have to heavily edit",
            "Complexity creep — platform has become bloated; new reps face a 4-6 week ramp time",
            "Focused on volume (send more emails) rather than quality (send better emails)",
            "Limited competitive intelligence — no battle card or prospect research capabilities",
            "Customer success varies dramatically by account size; SMB accounts feel neglected",
        ],
        "your_differentiators": [
            "We focus on research quality first, outreach volume second — better input = better output",
            "AI-generated content is deeply personalized using prospect research, not just mail merge tokens",
            "Built-in deal scoring uses NLP on deal notes — Outreach requires separate tools for this",
            "Battle card generation is native — Outreach has no competitive intelligence features",
            "Our platform costs 60% less while covering research, outreach, scoring, AND competitive intel",
        ],
        "when_you_win": [
            "Prospect's reps complain that Outreach emails 'all sound the same' despite personalization tokens",
            "Team needs research + outreach in one workflow, not two separate tools",
            "Budget-conscious mid-market team can't justify $150/user/month for Outreach",
            "Sales leadership wants competitive intelligence alongside engagement — not as a separate purchase",
        ],
        "when_you_lose": [
            "Prospect is an enterprise with 500+ reps and needs Outreach's scaled infrastructure",
            "Deep Salesforce workflow automation is the primary buying criteria",
            "Prospect already has 2+ year Outreach contract with significant switching costs",
            "Conversation intelligence (Kaia) is the primary use case, not outreach personalization",
        ],
        "objection_handling": [
            {
                "objection": "Outreach is the market leader — why would we go with a smaller player?",
                "response": "Market leadership in email volume doesn't mean leadership in email quality. Outreach optimizes for 'send more'; we optimize for 'send better.' The result is higher reply rates with fewer sends.",
                "proof_point": "Our clients see 3.2x higher reply rates because every email is backed by AI-driven prospect research, not just name/company merge fields.",
            },
            {
                "objection": "We've already invested in Outreach and our team is trained on it.",
                "response": "We're complementary, not a replacement. Most teams use us for the research and competitive intel layer, then feed higher-quality context into their existing Outreach sequences.",
                "proof_point": "38% of our customers use us alongside Outreach — they report that research-informed sequences outperform standard ones by 2.5x.",
            },
            {
                "objection": "Outreach has AI email features too — Smart Email Assist.",
                "response": "Smart Email Assist generates from templates and CRM fields. Our AI researches the actual company — news, pain points, competitive dynamics — and writes from that context. The depth difference is immediately visible.",
                "proof_point": "Side-by-side blind test: 78% of sales leaders rated our AI-generated emails as 'significantly more personalized' than Outreach Smart Email Assist output.",
            },
        ],
        "elevator_pitch_vs_competitor": (
            "Outreach helps you send more emails faster. We help you send better emails "
            "that actually get replies. By combining AI-powered prospect research, deep "
            "personalization, deal scoring, and competitive intelligence in one platform, "
            "we give your reps the context they need before they ever hit send. The result: "
            "fewer emails, higher reply rates, and deals that close faster."
        ),
        "trap_questions": [
            "Can you show me two Outreach-generated emails for different prospects in the same industry? How different are they really?",
            "What does Outreach use as input for personalization beyond CRM fields and LinkedIn data?",
            "How does your team currently research a prospect before adding them to a sequence?",
            "What's your cost per booked meeting — has it improved or worsened as you've scaled sends?",
        ],
        "landmine_questions": [
            "How many emails can your platform send per day?",
            "Do you have native Salesforce activity logging?",
            "What's your conversation intelligence offering?",
        ],
        "landmine_responses": [
            "We optimize for reply rate, not send volume. Our clients send 40% fewer emails but book 30% more meetings. If your goal is volume, Outreach is the right tool. If your goal is conversion, let's talk.",
            "We integrate with Salesforce for CRM data enrichment and research context. For activity logging, we complement your existing engagement tool rather than replacing it.",
            "Conversation intelligence is a different problem. We focus on the pre-conversation layer: research, preparation, and competitive positioning. This makes every conversation more productive regardless of which CI tool you use.",
        ],
    },
}


def _build_generic_card(competitor: str, product: Dict) -> Dict:
    """
    Generate a plausible generic battle card for competitors not in the
    mock data.  Ensures the demo never fails regardless of input.
    """
    return {
        "competitor": competitor,
        "competitor_overview": (
            f"{competitor} is an established player in the market. They offer a "
            f"competitive solution that appeals to enterprises seeking proven, scalable "
            f"platforms. Their strength lies in brand recognition and existing market share, "
            f"while their weakness is often slower innovation and less flexibility for "
            f"mid-market buyers."
        ),
        "competitor_strengths": [
            "Established brand with strong market recognition and enterprise trust",
            "Large customer base provides social proof and reference-ability",
            "Mature product with broad feature set built over many years",
            "Strong partner ecosystem and integration marketplace",
            "Well-funded with significant R&D investment capability",
        ],
        "competitor_weaknesses": [
            "Innovation speed is slower — large codebase and legacy architecture create drag",
            "Pricing tends to be enterprise-focused, making it expensive for mid-market",
            "AI/ML capabilities are often bolt-on acquisitions, not natively integrated",
            "Customer support quality varies significantly by account tier",
            "Configuration complexity requires dedicated admin resources",
        ],
        "your_differentiators": [
            "AI-native architecture — our platform was built around AI from day one, not retrofitted",
            "Research-first approach means every action is informed by real prospect context",
            "Unified platform for research, outreach, scoring, and competitive intel — not point solutions",
            "Mid-market pricing with enterprise capabilities — 40-60% lower TCO",
            "Faster time-to-value — teams are productive in days, not weeks",
        ],
        "when_you_win": [
            f"Prospect is frustrated with {competitor}'s complexity and long implementation timelines",
            "AI-powered personalization and research depth are evaluated in a live demo",
            "Budget-conscious buyer needs enterprise features without enterprise pricing",
            "Prospect values innovation speed and a modern technology stack",
        ],
        "when_you_lose": [
            f"Prospect has a deep existing integration with {competitor} and high switching costs",
            f"{competitor} offers aggressive discounting or multi-year lock-in pricing",
            "Prospect's evaluation criteria favor feature breadth over feature depth",
            "CIO mandate for vendor consolidation favors the incumbent",
        ],
        "objection_handling": [
            {
                "objection": f"We've been with {competitor} for years — why switch?",
                "response": f"We're not asking you to rip and replace. Start with our AI research and competitive intel layer alongside {competitor}. Most clients see value in week one and expand from there.",
                "proof_point": f"42% of our enterprise clients started as a complement to {competitor} before expanding to our full platform.",
            },
            {
                "objection": f"{competitor} has more features.",
                "response": "More features doesn't mean more value. We focus on the features that actually move pipeline — research, personalization, and competitive intelligence. Every feature we build is tied to a revenue outcome.",
                "proof_point": "Our clients report using 90% of our features regularly, compared to industry average of 40% for legacy platforms.",
            },
            {
                "objection": f"{competitor} is the safer choice.",
                "response": "Safe for the procurement committee, maybe. But safe for your quota? The risk is standing still while competitors adopt AI-native tools. We help your team perform at a level the old tools can't match.",
                "proof_point": "Teams using our platform exceed quota at 1.4x the rate of teams using legacy tools — because they're better prepared for every conversation.",
            },
        ],
        "elevator_pitch_vs_competitor": (
            f"{competitor} was built for the last era of sales — more activity, more emails, "
            f"more calls. We're built for this era: smarter research, deeper personalization, "
            f"and AI-powered competitive intelligence. The result is fewer touchpoints that "
            f"convert at higher rates, with every rep performing like your best rep."
        ),
        "trap_questions": [
            f"How has {competitor}'s AI strategy evolved in the last 12 months — is it native or acquired?",
            "What's your average rep ramp time on the platform, and how does that compare to when you started?",
            f"Can you show me how {competitor}'s personalization goes beyond mail merge tokens?",
            f"What does {competitor}'s roadmap look like for AI-native features — is it a retrofit or a rebuild?",
        ],
        "landmine_questions": [
            "How long have you been in the market?",
            "How many enterprise customers do you have?",
            "Can you match our existing workflow exactly?",
        ],
        "landmine_responses": [
            "We're newer to market, which is our advantage — we built on modern AI infrastructure from day one. No legacy debt, no retrofitting, no compromise. The question isn't how long we've existed; it's how fast we can move.",
            "We focus on customer outcomes, not customer count. Our NPS is 72 (vs. industry average of 36) because every account gets the attention it deserves.",
            "We don't try to replicate legacy workflows — we replace them with better ones. Our clients don't want to do the same thing on a new platform; they want to do something fundamentally better.",
        ],
    }


# ---------------------------------------------------------------------------
# Core generation function — entry point for CLI, Streamlit, and
# programmatic use.
# ---------------------------------------------------------------------------

def generate_battle_card(
    competitor: str,
    product_context: Optional[Dict] = None,
    *,
    mode: str = "mock",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
) -> BattleCard:
    """
    Generate a competitive battle card for the given competitor.

    Parameters
    ----------
    competitor : str
        Name of the competitor to analyze.
    product_context : dict, optional
        Your product information (name, category, capabilities).
        Defaults to the AdTech Solutions demo product.
    mode : str
        "mock" (default) or "live" for API-based generation.
    api_key, api_base, model : str, optional
        API configuration for live mode.

    Returns
    -------
    BattleCard
        Complete competitive battle card.
    """
    product = product_context or DEFAULT_PRODUCT

    if mode == "mock":
        return _generate_mock(competitor, product)
    elif mode == "live":
        return _generate_live(competitor, product, api_key=api_key,
                              api_base=api_base, model=model)
    else:
        raise ValueError(f"Unknown mode '{mode}'. Use 'mock' or 'live'.")


def _generate_mock(competitor: str, product: Dict) -> BattleCard:
    """Return a mock battle card from pre-built data or generic template."""
    key = competitor.strip().lower()
    data = _MOCK_CARDS.get(key, _build_generic_card(competitor, product))

    # Convert objection handling dicts to ObjectionResponse dataclasses
    objections = [
        ObjectionResponse(**o) if isinstance(o, dict) else o
        for o in data.get("objection_handling", [])
    ]

    return BattleCard(
        your_product=product.get("name", "Our Product"),
        competitor=data["competitor"],
        competitor_overview=data["competitor_overview"],
        competitor_strengths=data["competitor_strengths"],
        competitor_weaknesses=data["competitor_weaknesses"],
        your_differentiators=data["your_differentiators"],
        when_you_win=data["when_you_win"],
        when_you_lose=data["when_you_lose"],
        objection_handling=objections,
        elevator_pitch_vs_competitor=data["elevator_pitch_vs_competitor"],
        trap_questions=data["trap_questions"],
        landmine_questions=data["landmine_questions"],
        landmine_responses=data["landmine_responses"],
    )


def _generate_live(
    competitor: str,
    product: Dict,
    *,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
) -> BattleCard:
    """
    Use an OpenAI-compatible API to generate a battle card.
    Requires the `openai` package.
    """
    resolved_key = api_key or os.getenv("OPENAI_API_KEY", "")
    resolved_base = api_base or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-4o")

    if not resolved_key:
        raise EnvironmentError(
            "Live mode requires an API key. Set OPENAI_API_KEY or pass api_key=."
        )

    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        raise ImportError("Live mode requires 'openai'. Install: pip install openai")

    system_prompt = textwrap.dedent(f"""\
        You are a competitive intelligence analyst for sales teams.
        Generate a battle card comparing our product against a competitor.

        Our product: {json.dumps(product)}

        Return JSON matching this schema:
        {{
          "competitor": "string",
          "competitor_overview": "string (3-4 sentences)",
          "competitor_strengths": ["string (5 items)"],
          "competitor_weaknesses": ["string (5-6 items)"],
          "your_differentiators": ["string (5 items)"],
          "when_you_win": ["string (4 items)"],
          "when_you_lose": ["string (4 items)"],
          "objection_handling": [
            {{
              "objection": "string",
              "response": "string",
              "proof_point": "string"
            }}
            // 3 items
          ],
          "elevator_pitch_vs_competitor": "string (3-4 sentences)",
          "trap_questions": ["string (4 items)"],
          "landmine_questions": ["string (3 items)"],
          "landmine_responses": ["string (3 items)"]
        }}

        Be specific, tactical, and actionable. Return ONLY valid JSON.
    """)

    client = OpenAI(api_key=resolved_key, base_url=resolved_base)
    response = client.chat.completions.create(
        model=resolved_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate battle card against: {competitor}"},
        ],
        temperature=0.4,
        max_tokens=3000,
    )

    data = json.loads(response.choices[0].message.content.strip())
    objections = [ObjectionResponse(**o) for o in data.get("objection_handling", [])]

    return BattleCard(
        your_product=product.get("name", "Our Product"),
        competitor=data["competitor"],
        competitor_overview=data["competitor_overview"],
        competitor_strengths=data["competitor_strengths"],
        competitor_weaknesses=data["competitor_weaknesses"],
        your_differentiators=data["your_differentiators"],
        when_you_win=data["when_you_win"],
        when_you_lose=data["when_you_lose"],
        objection_handling=objections,
        elevator_pitch_vs_competitor=data["elevator_pitch_vs_competitor"],
        trap_questions=data["trap_questions"],
        landmine_questions=data["landmine_questions"],
        landmine_responses=data["landmine_responses"],
    )


# ---------------------------------------------------------------------------
# Standalone execution for quick testing.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a competitive battle card")
    parser.add_argument("--competitor", default="Google Ads",
                        help="Competitor to analyze")
    args = parser.parse_args()

    card = generate_battle_card(args.competitor)
    print(card.to_markdown())
