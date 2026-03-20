#!/usr/bin/env python3
"""
run_tools.py
────────────
CLI runner for the AI Sales Enablement toolkit.

Provides a unified command-line interface to all four tools:
  • research     — Prospect research briefs
  • personalize  — Outreach email personalization
  • score        — Deal qualification scoring
  • battlecard   — Competitive battle card generation

All tools run in mock mode by default (no API keys needed).

Usage:
    python run_tools.py research "Snap Inc"
    python run_tools.py personalize --prospect "Snap Inc" --template cold_intro
    python run_tools.py score --notes "Met with VP Marketing, interested in Q3 launch..."
    python run_tools.py battlecard --competitor "Google Ads"

For live mode (requires API key):
    OPENAI_API_KEY=sk-... python run_tools.py research "HubSpot" --mode live
"""

from __future__ import annotations

import argparse
import json
import sys

from tools.prospect_researcher import research_prospect
from tools.outreach_personalizer import personalize_outreach, TEMPLATES
from tools.deal_scorer import score_deal
from tools.battle_card_generator import generate_battle_card


# ---------------------------------------------------------------------------
# CLI argument parser — each subcommand maps to one tool.
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """
    Construct the argument parser with subcommands for each tool.
    Each subcommand has its own set of flags tailored to the tool's inputs.
    """
    parser = argparse.ArgumentParser(
        prog="run_tools",
        description="AI Sales Enablement Toolkit — CLI Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tools.py research "Snap Inc"
  python run_tools.py personalize --prospect "HubSpot" --template warm_referral
  python run_tools.py score --notes "Budget approved, meeting with CRO next week"
  python run_tools.py battlecard --competitor "Outreach.io"
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Tool to run")

    # ── Research subcommand ──
    research_parser = subparsers.add_parser(
        "research",
        help="Generate a prospect research brief for a company",
    )
    research_parser.add_argument(
        "company",
        help="Company name to research (e.g., 'Snap Inc')",
    )
    research_parser.add_argument(
        "--mode", default="mock", choices=["mock", "live"],
        help="Run mode: 'mock' (default, no API key) or 'live' (requires API key)",
    )
    research_parser.add_argument(
        "--format", default="markdown", choices=["markdown", "json"],
        help="Output format: 'markdown' (default) or 'json'",
    )

    # ── Personalize subcommand ──
    personalize_parser = subparsers.add_parser(
        "personalize",
        help="Generate a personalized outreach email",
    )
    personalize_parser.add_argument(
        "--prospect", required=True,
        help="Company name for the prospect",
    )
    personalize_parser.add_argument(
        "--template", default="cold_intro",
        choices=list(TEMPLATES.keys()),
        help="Outreach template to use (default: cold_intro)",
    )
    personalize_parser.add_argument(
        "--mode", default="mock", choices=["mock", "live"],
        help="Run mode: 'mock' (default) or 'live'",
    )
    personalize_parser.add_argument(
        "--format", default="markdown", choices=["markdown", "json"],
        help="Output format",
    )

    # ── Score subcommand ──
    score_parser = subparsers.add_parser(
        "score",
        help="Score deal qualification from free-text notes",
    )
    score_parser.add_argument(
        "--notes", required=True,
        help="Free-text deal notes to analyze (quote the entire string)",
    )
    score_parser.add_argument(
        "--format", default="markdown", choices=["markdown", "json"],
        help="Output format",
    )

    # ── Battle card subcommand ──
    battlecard_parser = subparsers.add_parser(
        "battlecard",
        help="Generate a competitive battle card",
    )
    battlecard_parser.add_argument(
        "--competitor", required=True,
        help="Competitor name to analyze",
    )
    battlecard_parser.add_argument(
        "--mode", default="mock", choices=["mock", "live"],
        help="Run mode: 'mock' (default) or 'live'",
    )
    battlecard_parser.add_argument(
        "--format", default="markdown", choices=["markdown", "json"],
        help="Output format",
    )

    return parser


# ---------------------------------------------------------------------------
# Command handlers — each function runs its tool and outputs the result.
# ---------------------------------------------------------------------------

def handle_research(args: argparse.Namespace) -> None:
    """Run the prospect researcher tool and print output."""
    brief = research_prospect(args.company, mode=args.mode)

    if args.format == "json":
        print(json.dumps(brief.to_dict(), indent=2))
    else:
        print(brief.to_markdown())


def handle_personalize(args: argparse.Namespace) -> None:
    """Run the outreach personalizer tool and print output."""
    result = personalize_outreach(
        company=args.prospect,
        template=args.template,
        mode=args.mode,
    )

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.to_markdown())


def handle_score(args: argparse.Namespace) -> None:
    """Run the deal scorer tool and print output."""
    result = score_deal(args.notes)

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.to_markdown())


def handle_battlecard(args: argparse.Namespace) -> None:
    """Run the battle card generator tool and print output."""
    card = generate_battle_card(args.competitor, mode=args.mode)

    if args.format == "json":
        print(json.dumps(card.to_dict(), indent=2))
    else:
        print(card.to_markdown())


# ---------------------------------------------------------------------------
# Main entry point — parse args and dispatch to the appropriate handler.
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse CLI arguments and execute the requested tool."""
    parser = build_parser()
    args = parser.parse_args()

    # If no subcommand was provided, print help and exit
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch table maps subcommand names to their handler functions
    handlers = {
        "research": handle_research,
        "personalize": handle_personalize,
        "score": handle_score,
        "battlecard": handle_battlecard,
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
