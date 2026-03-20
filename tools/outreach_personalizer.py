"""
tools/outreach_personalizer.py
──────────────────────────────
AI-powered outreach personalization engine.

Takes prospect research (from prospect_researcher), an outreach template
name, and sender context to produce a personalized email with a quality
scoring rubric.

Templates cover five common sales scenarios:
  1. cold_intro     — First touch to a cold prospect
  2. warm_referral  — Leveraging a mutual connection
  3. event_followup — Post-conference or webinar follow-up
  4. renewal        — Contract renewal with expansion angle
  5. upsell         — Cross-sell / upsell to existing customer

Supports mock mode (default) and live mode (OpenAI-compatible API).

Usage (standalone):
    python -m tools.outreach_personalizer --prospect "Snap Inc" --template cold_intro
"""

from __future__ import annotations

import json
import os
import textwrap
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

from tools.prospect_researcher import ProspectBrief, research_prospect


# ---------------------------------------------------------------------------
# Data model — every personalized outreach includes the email body plus a
# quality scoring rubric so teams can evaluate and iterate on output.
# ---------------------------------------------------------------------------

@dataclass
class OutreachScore:
    """Quality rubric for a personalized outreach email."""
    specificity_score: int          # 1-10: how specific is the personalization?
    personalization_depth: int      # 1-10: does it reference real prospect context?
    cta_clarity: int                # 1-10: is the call-to-action clear and low-friction?
    tone_appropriateness: int       # 1-10: professional yet human, not robotic?
    overall_score: int              # 1-100: weighted composite
    improvement_suggestions: List[str]


@dataclass
class PersonalizedOutreach:
    """Complete personalized outreach package — email plus scoring rubric."""
    prospect_company: str
    template_used: str
    subject_line: str
    email_body: str
    score: OutreachScore
    sender_context: Dict[str, str]

    def to_dict(self) -> Dict:
        """Serialize to a plain dictionary for JSON output."""
        return asdict(self)

    def to_markdown(self) -> str:
        """Render as a human-readable Markdown document."""
        # Build the improvement suggestions as a bullet list
        suggestions = "\n".join(
            f"- {s}" for s in self.score.improvement_suggestions
        )

        return textwrap.dedent(f"""\
        # Personalized Outreach — {self.prospect_company}

        **Template:** {self.template_used}
        **From:** {self.sender_context.get('name', 'Sales Rep')} · {self.sender_context.get('title', '')} · {self.sender_context.get('company', '')}

        ---

        **Subject:** {self.subject_line}

        {self.email_body}

        ---

        ## Quality Score: {self.score.overall_score}/100

        | Dimension | Score |
        |-----------|-------|
        | Specificity | {self.score.specificity_score}/10 |
        | Personalization Depth | {self.score.personalization_depth}/10 |
        | CTA Clarity | {self.score.cta_clarity}/10 |
        | Tone | {self.score.tone_appropriateness}/10 |

        ### Suggestions for Improvement
        {suggestions}
        """)


# ---------------------------------------------------------------------------
# Template definitions — each template provides a skeleton that gets filled
# with prospect-specific details.  The key is the template name used in CLI.
# ---------------------------------------------------------------------------

TEMPLATES: Dict[str, Dict[str, str]] = {
    "cold_intro": {
        "name": "Cold Introduction",
        "description": "First outreach to a prospect with no prior relationship.",
        "tone": "professional, concise, curiosity-driven",
    },
    "warm_referral": {
        "name": "Warm Referral",
        "description": "Outreach leveraging a mutual connection or shared network.",
        "tone": "warm, credible, relationship-forward",
    },
    "event_followup": {
        "name": "Event Follow-Up",
        "description": "Follow-up after meeting at a conference, webinar, or industry event.",
        "tone": "timely, specific to the event, action-oriented",
    },
    "renewal": {
        "name": "Renewal Outreach",
        "description": "Re-engagement for contract renewal with expansion opportunity.",
        "tone": "appreciative, results-oriented, forward-looking",
    },
    "upsell": {
        "name": "Upsell / Cross-Sell",
        "description": "Expanding an existing relationship with additional products or services.",
        "tone": "consultative, value-driven, low-pressure",
    },
}

# Default sender context used when none is provided — represents CJ's profile
_DEFAULT_SENDER = {
    "name": "CJ Fleming",
    "title": "Director of Sales",
    "company": "AdTech Solutions",
    "value_prop": "AI-powered sales enablement that increases pipeline velocity by 40%",
}


# ---------------------------------------------------------------------------
# Mock outreach generation — pre-built, high-quality personalized emails
# that demonstrate the tool's capabilities without needing an API key.
# ---------------------------------------------------------------------------

def _generate_mock_outreach(
    brief: ProspectBrief,
    template_key: str,
    sender: Dict[str, str],
) -> PersonalizedOutreach:
    """
    Build a realistic mock personalized email using prospect research
    and the selected template.  The output is hand-tuned to look like
    production-quality AI-generated outreach.
    """
    # Extract the first pain point and first approach angle from research
    # to inject genuine personalization into the email body
    primary_pain = brief.pain_points[0] if brief.pain_points else "operational efficiency"
    primary_angle = brief.recommended_angles[0] if brief.recommended_angles else "driving measurable outcomes"
    first_news = brief.recent_news[0] if brief.recent_news else "recent strategic initiatives"
    first_contact = brief.key_contacts_to_target[0] if brief.key_contacts_to_target else "your team"

    # Helper to lowercase only the first character — preserves proper nouns
    # and acronyms in the rest of the string (e.g., "Launched Snap AR..." →
    # "launched Snap AR...")
    def _lc(s: str) -> str:
        return s[0].lower() + s[1:] if s else s

    # ── Template-specific email content ──
    # Each template generates a different email structure and tone
    if template_key == "cold_intro":
        subject = f"Quick thought on {brief.company}'s {brief.industry.split('/')[0].strip()} strategy"
        body = textwrap.dedent(f"""\
            Hi there,

            I saw that {brief.company} recently {_lc(first_news)} — it signals exactly
            the kind of strategic shift where teams like yours tend to hit a scaling
            challenge: {_lc(primary_pain)}.

            We've helped companies in {brief.industry.split('/')[0].strip()} solve this by
            {sender.get('value_prop', 'driving measurable outcomes')}. One client in a
            similar position saw a 3x improvement in outbound conversion within 90 days.

            Would a 15-minute call next week make sense to see if there's a fit? I can
            share the specific playbook we used.

            Best,
            {sender.get('name', 'CJ')}
            {sender.get('title', '')} · {sender.get('company', '')}""")
        score = OutreachScore(
            specificity_score=8, personalization_depth=7, cta_clarity=9,
            tone_appropriateness=8, overall_score=82,
            improvement_suggestions=[
                "Add a specific metric from the prospect's recent earnings to increase specificity",
                "Reference the exact role title of the intended recipient for stronger personalization",
                "Consider adding a P.S. line with a relevant case study link",
            ],
        )

    elif template_key == "warm_referral":
        subject = f"[Intro via Sarah Chen] Idea for {brief.company}'s sales enablement"
        body = textwrap.dedent(f"""\
            Hi there,

            Sarah Chen (VP Partnerships at TechForward) suggested I reach out — she
            mentioned that {brief.company} is navigating {_lc(primary_pain)},
            and thought there might be alignment with what we're doing at
            {sender.get('company', 'our company')}.

            Quick context: {sender.get('value_prop', 'we help revenue teams scale with AI')}.
            Given that {brief.company} recently {_lc(first_news)}, I think there's a
            strong opportunity to {_lc(primary_angle)}.

            Sarah offered to make a warm intro, but I wanted to reach out directly
            first. Would you be open to a quick 20-minute conversation this week?

            Best,
            {sender.get('name', 'CJ')}
            {sender.get('title', '')} · {sender.get('company', '')}""")
        score = OutreachScore(
            specificity_score=8, personalization_depth=9, cta_clarity=8,
            tone_appropriateness=9, overall_score=87,
            improvement_suggestions=[
                "Verify the mutual connection is comfortable being named before sending",
                "Add one specific result metric to make the value prop more tangible",
                "Consider making the CTA even more specific (propose an exact date/time)",
            ],
        )

    elif template_key == "event_followup":
        subject = f"Great connecting at AdTech Summit — {brief.company} + AI enablement"
        body = textwrap.dedent(f"""\
            Hi there,

            It was great connecting at AdTech Summit last week. Your comments during
            the panel on "Scaling Revenue Operations" really resonated — especially
            the point about {_lc(primary_pain)}.

            I've been thinking about what you shared, and it maps closely to a
            challenge we recently solved for a {brief.industry.split('/')[0].strip()} company:
            {sender.get('value_prop', 'AI-augmented sales workflows')}.

            I put together a short brief on how {brief.company} could apply a similar
            approach — especially now that you've {_lc(first_news)}. Happy to share it over
            a quick call — or I can just send the doc if that's easier.

            Looking forward to continuing the conversation.

            Best,
            {sender.get('name', 'CJ')}
            {sender.get('title', '')} · {sender.get('company', '')}""")
        score = OutreachScore(
            specificity_score=9, personalization_depth=8, cta_clarity=9,
            tone_appropriateness=9, overall_score=89,
            improvement_suggestions=[
                "Reference the exact panel or session title for stronger recall",
                "Attach the brief mentioned in the email to reduce friction",
                "Add a LinkedIn connection request as a parallel touch",
            ],
        )

    elif template_key == "renewal":
        subject = f"Renewing our partnership — new capabilities for {brief.company}"
        body = textwrap.dedent(f"""\
            Hi there,

            As we approach the renewal window for {brief.company}'s account, I wanted
            to share some updates that are directly relevant to what your team has
            been working on.

            Over the past year, we've seen {brief.company} make impressive moves —
            particularly having {_lc(first_news)}. On our side, we've shipped new
            capabilities around {sender.get('value_prop', 'AI-powered enablement')} that
            align perfectly with where you're headed.

            Specifically, I think we can help address {_lc(primary_pain)} — a
            challenge that's come up in our quarterly reviews and one we now have a
            much stronger solution for.

            Can we schedule 30 minutes to walk through the new roadmap and discuss
            terms? I'd also love to get your input on what's working and what we
            can improve.

            Best,
            {sender.get('name', 'CJ')}
            {sender.get('title', '')} · {sender.get('company', '')}""")
        score = OutreachScore(
            specificity_score=7, personalization_depth=8, cta_clarity=8,
            tone_appropriateness=9, overall_score=83,
            improvement_suggestions=[
                "Include specific ROI metrics from the current contract period",
                "Reference the exact renewal date to create appropriate urgency",
                "Mention a specific new feature that maps to their stated pain point",
            ],
        )

    else:  # upsell
        subject = f"New opportunity for {brief.company} — expanding what's working"
        body = textwrap.dedent(f"""\
            Hi there,

            I've been reviewing {brief.company}'s usage data from the past quarter,
            and I noticed something interesting: your team is consistently hitting
            the ceiling on [current product tier], which tells me you're getting
            real value from the platform.

            Given that {brief.company} recently {_lc(first_news)}, I think
            there's a natural expansion opportunity. Our [advanced tier / new module]
            specifically addresses {_lc(primary_pain)} — which I know has been
            a priority for the {_lc(first_contact)}.

            I've mapped out a quick ROI model showing the expected impact. Would
            it be helpful to walk through it together? Should take about 20 minutes.

            Best,
            {sender.get('name', 'CJ')}
            {sender.get('title', '')} · {sender.get('company', '')}""")
        score = OutreachScore(
            specificity_score=7, personalization_depth=7, cta_clarity=9,
            tone_appropriateness=8, overall_score=80,
            improvement_suggestions=[
                "Replace placeholder [current product tier] with actual product name",
                "Include the specific usage metric that indicates expansion readiness",
                "Add a brief customer story from a similar account that expanded successfully",
            ],
        )

    return PersonalizedOutreach(
        prospect_company=brief.company,
        template_used=TEMPLATES[template_key]["name"],
        subject_line=subject,
        email_body=body,
        score=score,
        sender_context=sender,
    )


# ---------------------------------------------------------------------------
# Core personalization function — entry point for CLI, Streamlit, and
# programmatic use.
# ---------------------------------------------------------------------------

def personalize_outreach(
    company: str,
    template: str = "cold_intro",
    sender_context: Optional[Dict[str, str]] = None,
    *,
    mode: str = "mock",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
    prospect_brief: Optional[ProspectBrief] = None,
) -> PersonalizedOutreach:
    """
    Generate a personalized outreach email for a prospect.

    Parameters
    ----------
    company : str
        Target company name.
    template : str
        Template key (cold_intro, warm_referral, event_followup, renewal, upsell).
    sender_context : dict, optional
        Info about the sender (name, title, company, value_prop).
        Defaults to CJ Fleming's profile.
    mode : str
        "mock" (default) or "live".
    api_key, api_base, model : str, optional
        API configuration for live mode.
    prospect_brief : ProspectBrief, optional
        Pre-computed research brief. If not provided, runs prospect_researcher
        first to gather context.

    Returns
    -------
    PersonalizedOutreach
        The personalized email with quality scoring rubric.
    """
    # Validate the template key exists in our template library
    if template not in TEMPLATES:
        available = ", ".join(TEMPLATES.keys())
        raise ValueError(f"Unknown template '{template}'. Available: {available}")

    # Use provided sender context or fall back to default profile
    sender = sender_context or _DEFAULT_SENDER

    # Get prospect research — either use what was passed in or generate it
    if prospect_brief is None:
        brief = research_prospect(company, mode=mode, api_key=api_key,
                                  api_base=api_base, model=model)
    else:
        brief = prospect_brief

    if mode == "mock":
        return _generate_mock_outreach(brief, template, sender)
    elif mode == "live":
        return _generate_live_outreach(brief, template, sender,
                                       api_key=api_key, api_base=api_base,
                                       model=model)
    else:
        raise ValueError(f"Unknown mode '{mode}'. Use 'mock' or 'live'.")


def _generate_live_outreach(
    brief: ProspectBrief,
    template_key: str,
    sender: Dict[str, str],
    *,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
) -> PersonalizedOutreach:
    """
    Use an OpenAI-compatible API to generate a personalized outreach email
    and score it.  Requires the `openai` package.
    """
    # ── Resolve configuration ──
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

    template_info = TEMPLATES[template_key]
    brief_json = json.dumps(brief.to_dict(), indent=2)

    system_prompt = textwrap.dedent(f"""\
        You are an expert sales copywriter. Given prospect research and a
        template type, write a personalized outreach email and score it.

        Template: {template_info['name']}
        Description: {template_info['description']}
        Tone: {template_info['tone']}

        Sender: {json.dumps(sender)}

        Return JSON matching this schema:
        {{
          "subject_line": "string",
          "email_body": "string",
          "score": {{
            "specificity_score": int (1-10),
            "personalization_depth": int (1-10),
            "cta_clarity": int (1-10),
            "tone_appropriateness": int (1-10),
            "overall_score": int (1-100),
            "improvement_suggestions": ["string (3 items)"]
          }}
        }}

        Rules:
        - Reference specific details from the prospect research
        - Keep the email under 200 words
        - Make the CTA specific and low-friction
        - Return ONLY valid JSON
    """)

    client = OpenAI(api_key=resolved_key, base_url=resolved_base)
    response = client.chat.completions.create(
        model=resolved_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Prospect research:\n{brief_json}"},
        ],
        temperature=0.5,
        max_tokens=1500,
    )

    data = json.loads(response.choices[0].message.content.strip())
    return PersonalizedOutreach(
        prospect_company=brief.company,
        template_used=template_info["name"],
        subject_line=data["subject_line"],
        email_body=data["email_body"],
        score=OutreachScore(**data["score"]),
        sender_context=sender,
    )


# ---------------------------------------------------------------------------
# Standalone execution for quick testing.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Personalize outreach for a prospect")
    parser.add_argument("--prospect", default="Snap Inc", help="Company name")
    parser.add_argument("--template", default="cold_intro",
                        choices=list(TEMPLATES.keys()), help="Template to use")
    args = parser.parse_args()

    result = personalize_outreach(args.prospect, template=args.template)
    print(result.to_markdown())
