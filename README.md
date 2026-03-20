# AI Sales Enablement Playbook

**A documented GenAI workflow with working Python tools for prospecting, outreach personalization, deal qualification, and competitive intelligence.**

Built by [CJ Fleming](https://linkedin.com) — 15+ years in media sales leadership, Columbia AI certification.

---

## What This Demonstrates

| Competency | How It's Demonstrated |
|---|---|
| **GenAI Enablement** | Operationalized AI workflows that a sales team can adopt tomorrow |
| **Sales Operations** | BANT/MEDDIC qualification scoring, pipeline review integration, ROI measurement |
| **Prompt Engineering** | Structured prompt templates for research, personalization, and competitive analysis |
| **Workflow Design** | End-to-end playbook mapping manual processes to AI-augmented equivalents |
| **Technical Execution** | Working Python tools with CLI and Streamlit interfaces, clean architecture |
| **Strategic Thinking** | Implementation roadmap, tool selection matrix, privacy framework, A/B testing design |

---

## Project Structure

```
ai-sales-playbook/
├── README.md                    # You are here
├── playbook/
│   └── README.md                # The full 5-chapter playbook document
├── tools/
│   ├── __init__.py
│   ├── prospect_researcher.py   # AI-augmented prospect research briefs
│   ├── outreach_personalizer.py # Template-based email personalization + scoring
│   ├── deal_scorer.py           # BANT qualification scoring (pure Python, no LLM)
│   └── battle_card_generator.py # Competitive battle card generation
├── run_tools.py                 # CLI runner for all tools
├── app.py                       # Streamlit demo application
├── run.sh                       # One-command app launcher
└── requirements.txt             # Python dependencies
```

---

## Quick Start

### Option 1: Streamlit App (recommended for demos)

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the app
./run.sh
```

The app opens at `http://localhost:8501` with four interactive tabs — one per tool. Everything runs in **mock mode by default** (no API keys required).

### Option 2: CLI

```bash
# Prospect research
python run_tools.py research "Snap Inc"
python run_tools.py research "HubSpot" --format json

# Outreach personalization
python run_tools.py personalize --prospect "Snap Inc" --template cold_intro
python run_tools.py personalize --prospect "HubSpot" --template warm_referral

# Deal qualification scoring
python run_tools.py score --notes "Met with VP Marketing, budget of \$150K approved, interested in Q3 pilot"

# Competitive battle cards
python run_tools.py battlecard --competitor "Google Ads"
python run_tools.py battlecard --competitor "Outreach.io" --format json
```

### Option 3: Live Mode (with API key)

All tools support live mode using any OpenAI-compatible API:

```bash
export OPENAI_API_KEY="sk-..."
python run_tools.py research "Salesforce" --mode live
```

Works with OpenAI, Anthropic (via proxy), Azure OpenAI, Ollama, and any other OpenAI-compatible endpoint.

---

## The Playbook

The [full playbook](playbook/README.md) is a 5-chapter strategic document covering:

| Chapter | Topic | Key Takeaway |
|---------|-------|-------------|
| 1 | AI-Augmented Prospecting | 80-90% time reduction per prospect with structured prompts |
| 2 | Personalized Outreach at Scale | Level 3 personalization at Level 1 speed; A/B testing framework |
| 3 | Deal Qualification & Scoring | BANT scoring with NLP pattern matching; CRM integration playbook |
| 4 | Competitive Intelligence | Battle card generation, win/loss analysis, competitor monitoring |
| 5 | Implementation Guide | Tool selection, privacy framework, ROI measurement, 90-day roadmap |

---

## The Tools

### Prospect Researcher

Generates structured research briefs including company overview, recent news, pain points, recommended approach angles, key contacts, and tech stack signals.

**Mock mode:** Pre-built briefs for Snap Inc and HubSpot; generates plausible generic briefs for any other company.

### Outreach Personalizer

Combines prospect research with five outreach templates (cold intro, warm referral, event follow-up, renewal, upsell) to produce personalized emails with a quality scoring rubric (specificity, personalization depth, CTA clarity, tone).

### Deal Scorer

Pure Python tool (no LLM required) that analyzes free-text deal notes using regex and keyword matching. Extracts BANT signals, flags risk factors, and generates recommended next actions. Deterministic, fast, and fully offline.

### Battle Card Generator

Produces structured competitive battle cards with strengths, weaknesses, differentiators, objection handling scripts, trap questions, and landmine responses. Mock data for Google Ads and Outreach.io.

---

## How This Maps to CJ's Career

This project is the bridge between **15 years of media sales leadership** and the **AI-enabled future of revenue organizations.**

- **The playbook** reflects hard-won operational knowledge: how pipeline reviews actually work, what makes outreach convert, why qualification matters more than activity metrics, and how to roll out new tools without breaking a sales team's rhythm.

- **The tools** demonstrate that AI enablement isn't theoretical. It's working code that a team can run today — with mock mode for stakeholder demos, live mode for production use, and a CLI for power users.

- **The architecture** shows a bias toward pragmatism: minimal dependencies, mock-first design, deterministic scoring where LLMs aren't needed, and structured output that integrates with existing CRM workflows.

This is what operationalizing AI for revenue teams looks like — not a pitch deck, not a proof of concept, but a documented system with working tools and a clear implementation path.

---

## Technical Details

- **Python 3.9+** required
- **Zero external dependencies** for CLI tools in mock mode
- **Streamlit** only dependency for the web demo
- **Optional:** `openai` package for live mode API calls
- All tools use **dataclasses** for structured output with `.to_dict()` and `.to_markdown()` methods
- Deal scorer uses **compiled regex** for pattern matching performance
- Architecture supports any **OpenAI-compatible API** (OpenAI, Anthropic, Azure, Ollama, etc.)
