"""
app.py
──────
Streamlit demo application for the AI Sales Enablement Playbook.

Provides an interactive web UI with four tabs — one for each tool in the
toolkit.  All tools run in mock mode by default so the app works without
any API keys.  This makes it ideal for portfolio demos and stakeholder
presentations.

Launch:
    streamlit run app.py
    # or
    ./run.sh
"""

from __future__ import annotations

import streamlit as st

from tools.prospect_researcher import research_prospect
from tools.outreach_personalizer import personalize_outreach, TEMPLATES
from tools.deal_scorer import score_deal
from tools.battle_card_generator import generate_battle_card


# ---------------------------------------------------------------------------
# Page configuration — sets the browser tab title, icon, and layout.
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Sales Enablement Playbook",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Sidebar — project context and mode selection.  The sidebar persists
# across all tabs so the user always has context about what they're using.
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("AI Sales Enablement")
    st.caption("By CJ Fleming")

    st.markdown("---")

    st.markdown("""
    **What is this?**

    A working GenAI toolkit for sales teams. Each tab demonstrates a
    different AI-augmented workflow:

    1. **Prospect Research** — AI-generated company briefs
    2. **Outreach Personalizer** — Template-based personalized emails
    3. **Deal Scorer** — BANT qualification from deal notes
    4. **Battle Cards** — Competitive intelligence generation

    All tools run in **mock mode** by default — no API keys required.
    """)

    st.markdown("---")

    # Mode selector — allows switching to live mode if an API key is provided
    mode = st.selectbox(
        "Mode",
        ["mock", "live"],
        index=0,
        help="Mock mode uses pre-built responses. Live mode calls an LLM API.",
    )

    # Only show API key input if live mode is selected
    api_key = None
    if mode == "live":
        api_key = st.text_input(
            "API Key",
            type="password",
            help="OpenAI-compatible API key for live mode",
        )
        if not api_key:
            st.warning("Live mode requires an API key.")

    st.markdown("---")
    st.markdown(
        "Built with Python & Streamlit | "
        "[View Playbook](playbook/README.md)"
    )


# ---------------------------------------------------------------------------
# Main content — tabbed interface with one tab per tool.
# ---------------------------------------------------------------------------

# Create the four tabs matching the four tools in the toolkit
tab_research, tab_outreach, tab_score, tab_battlecard = st.tabs([
    "🔍 Prospect Research",
    "✉️ Outreach Personalizer",
    "📊 Deal Scorer",
    "⚔️ Battle Cards",
])


# ═══════════════════════════════════════════════════════════════════════════
# Tab 1: Prospect Research
# Allows the user to enter a company name and receive a structured research
# brief.  The brief includes company overview, news, pain points, and
# recommended approach angles.
# ═══════════════════════════════════════════════════════════════════════════

with tab_research:
    st.header("AI-Augmented Prospect Research")
    st.markdown(
        "Enter a company name to generate a comprehensive research brief. "
        "The tool analyzes the company's industry, recent news, pain points, "
        "and recommends approach angles for your sales team."
    )

    # Input form with company name and a generate button
    col_input, col_spacer = st.columns([2, 1])
    with col_input:
        research_company = st.text_input(
            "Company Name",
            value="Snap Inc",
            placeholder="Enter a company name...",
            key="research_company",
        )

    # Generate button triggers the research
    if st.button("Generate Research Brief", key="btn_research", type="primary"):
        with st.spinner("Researching prospect..."):
            try:
                brief = research_prospect(
                    research_company,
                    mode=mode,
                    api_key=api_key,
                )

                # Display the brief as formatted Markdown
                st.markdown(brief.to_markdown())

                # Provide a JSON download option for CRM integration
                st.download_button(
                    label="Download as JSON",
                    data=__import__("json").dumps(brief.to_dict(), indent=2),
                    file_name=f"research_{research_company.lower().replace(' ', '_')}.json",
                    mime="application/json",
                )
            except Exception as e:
                st.error(f"Error generating research brief: {e}")

    # Show example output to help users understand what they'll get
    with st.expander("What does this tool do?"):
        st.markdown("""
        **Inputs:** Company name

        **Outputs:**
        - Company overview with industry, revenue, and headcount
        - Recent news and trigger events
        - Potential pain points relevant to your solution
        - Recommended approach angles for first outreach
        - Key contacts to target (by role)
        - Competitive landscape summary
        - Tech stack signals

        **How it works:**
        In mock mode, the tool returns pre-built research for known companies
        (Snap Inc, HubSpot) or generates a plausible generic brief for others.
        In live mode, it sends a structured prompt to an LLM API to generate
        real-time research.
        """)


# ═══════════════════════════════════════════════════════════════════════════
# Tab 2: Outreach Personalizer
# Combines prospect research with outreach templates to produce personalized
# emails complete with a quality scoring rubric.
# ═══════════════════════════════════════════════════════════════════════════

with tab_outreach:
    st.header("Personalized Outreach at Scale")
    st.markdown(
        "Combine prospect research with proven outreach templates to generate "
        "personalized emails. Each email is scored on specificity, personalization "
        "depth, CTA clarity, and tone."
    )

    # Two-column layout for inputs
    col_prospect, col_template = st.columns(2)

    with col_prospect:
        outreach_company = st.text_input(
            "Prospect Company",
            value="Snap Inc",
            placeholder="Enter company name...",
            key="outreach_company",
        )

    with col_template:
        # Template selector with descriptive labels
        template_options = {
            key: f"{info['name']} — {info['description']}"
            for key, info in TEMPLATES.items()
        }
        selected_template = st.selectbox(
            "Outreach Template",
            options=list(template_options.keys()),
            format_func=lambda x: template_options[x],
            key="outreach_template",
        )

    # Optional sender context customization
    with st.expander("Customize Sender Context (optional)"):
        sender_col1, sender_col2 = st.columns(2)
        with sender_col1:
            sender_name = st.text_input("Your Name", value="CJ Fleming", key="sender_name")
            sender_title = st.text_input("Your Title", value="Director of Sales", key="sender_title")
        with sender_col2:
            sender_company = st.text_input("Your Company", value="AdTech Solutions", key="sender_company")
            sender_value = st.text_input(
                "Value Proposition",
                value="AI-powered sales enablement that increases pipeline velocity by 40%",
                key="sender_value",
            )

    # Build sender context dict from form inputs
    sender_ctx = {
        "name": sender_name,
        "title": sender_title,
        "company": sender_company,
        "value_prop": sender_value,
    }

    if st.button("Generate Personalized Outreach", key="btn_outreach", type="primary"):
        with st.spinner("Personalizing outreach..."):
            try:
                result = personalize_outreach(
                    company=outreach_company,
                    template=selected_template,
                    sender_context=sender_ctx,
                    mode=mode,
                    api_key=api_key,
                )

                # Display the email and scoring rubric
                st.markdown(result.to_markdown())

                # Show the score as a visual metric row
                st.markdown("### Score Breakdown")
                metric_cols = st.columns(5)
                metric_cols[0].metric("Overall", f"{result.score.overall_score}/100")
                metric_cols[1].metric("Specificity", f"{result.score.specificity_score}/10")
                metric_cols[2].metric("Personalization", f"{result.score.personalization_depth}/10")
                metric_cols[3].metric("CTA Clarity", f"{result.score.cta_clarity}/10")
                metric_cols[4].metric("Tone", f"{result.score.tone_appropriateness}/10")

            except Exception as e:
                st.error(f"Error generating outreach: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# Tab 3: Deal Scorer
# Analyzes free-text deal notes using regex and keyword matching to extract
# BANT signals and flag risk factors.  No LLM required — fully deterministic.
# ═══════════════════════════════════════════════════════════════════════════

with tab_score:
    st.header("Deal Qualification & Scoring")
    st.markdown(
        "Paste deal notes from your CRM, call summaries, or email threads. "
        "The scorer extracts BANT (Budget, Authority, Need, Timeline) signals "
        "using NLP pattern matching and flags risk factors."
    )

    # Large text area for pasting deal notes
    default_notes = (
        "Met with VP Marketing at Snap Inc last Tuesday. They're very interested "
        "in launching a pilot in Q3 2025. Budget of $150K has been approved by "
        "the CMO for this initiative. Main pain point is scaling personalized "
        "outreach — their team currently spends 3 hours per prospect on manual "
        "research before any outreach happens.\n\n"
        "They're also evaluating a competitor (Outreach.io) but expressed concern "
        "about Outreach's pricing at $120/user/month for 80 reps. No internal "
        "champion identified yet on their side — need to get in front of the "
        "Director of Sales Enablement who would be the day-to-day user.\n\n"
        "Next steps: Send ROI calculator and case study from similar AdTech company. "
        "Follow-up call scheduled for next week with the VP and their RevOps lead."
    )

    deal_notes = st.text_area(
        "Deal Notes",
        value=default_notes,
        height=200,
        placeholder="Paste your deal notes here...",
        key="deal_notes",
    )

    if st.button("Score Deal", key="btn_score", type="primary"):
        if not deal_notes.strip():
            st.warning("Please enter deal notes to analyze.")
        else:
            with st.spinner("Analyzing deal notes..."):
                result = score_deal(deal_notes)

                # Visual score display with color coding based on grade
                grade_colors = {"A": "green", "B": "blue", "C": "orange", "D": "red", "F": "red"}
                grade_color = grade_colors.get(result.grade, "gray")

                # Score header with grade and stage
                st.markdown(
                    f"### Score: **{result.final_score}/100** "
                    f"(Grade: **{result.grade}**) — {result.qualification_stage}"
                )

                # BANT dimension scores as metrics
                bant_cols = st.columns(4)
                bant_cols[0].metric("Budget", f"{result.bant.budget_score}/25")
                bant_cols[1].metric("Authority", f"{result.bant.authority_score}/25")
                bant_cols[2].metric("Need", f"{result.bant.need_score}/25")
                bant_cols[3].metric("Timeline", f"{result.bant.timeline_score}/25")

                # Show risk deduction if applicable
                if result.risk_deduction > 0:
                    st.warning(f"Risk deduction: -{result.risk_deduction} points")

                # Full Markdown report
                st.markdown(result.to_markdown())


# ═══════════════════════════════════════════════════════════════════════════
# Tab 4: Battle Card Generator
# Generates structured competitive battle cards with strengths, weaknesses,
# objection handling, and tactical guidance.
# ═══════════════════════════════════════════════════════════════════════════

with tab_battlecard:
    st.header("Competitive Battle Card Generator")
    st.markdown(
        "Enter a competitor name to generate a structured battle card. "
        "Includes competitive analysis, objection handling scripts, "
        "trap questions, and positioning guidance."
    )

    col_comp, col_spacer2 = st.columns([2, 1])
    with col_comp:
        competitor_name = st.text_input(
            "Competitor Name",
            value="Google Ads",
            placeholder="Enter competitor name...",
            key="competitor_name",
        )

    # Suggest pre-built competitors for best demo experience
    st.caption("Try: 'Google Ads', 'Outreach.io', or any company name")

    if st.button("Generate Battle Card", key="btn_battlecard", type="primary"):
        with st.spinner("Generating battle card..."):
            try:
                card = generate_battle_card(
                    competitor_name,
                    mode=mode,
                    api_key=api_key,
                )

                # Display the full battle card as Markdown
                st.markdown(card.to_markdown())

                # Provide download option for sharing with the sales team
                st.download_button(
                    label="Download as JSON",
                    data=__import__("json").dumps(card.to_dict(), indent=2),
                    file_name=f"battlecard_{competitor_name.lower().replace(' ', '_')}.json",
                    mime="application/json",
                )
            except Exception as e:
                st.error(f"Error generating battle card: {e}")
