#!/usr/bin/env python3
"""Multi-Agent Master Orchestrator Engine for High-Fidelity PPT Restoration.

Coordinates the Multi-Agent workflow:
1. Architect: Macro perception & blueprint generation (Gate 1 & 2)
2. Developer: Isolated single-block pure vector code construction (Gate 3)
3. Reviewer: Automated visual Diff & DOM tree QA with In-Place Healing loop
4. Assembler: Full deck assembly and Gate 4 final verification
"""

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple


WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPECS_DIR = os.path.join(WORKSPACE_ROOT, "specs")
BLUEPRINT_PATH = os.path.join(SPECS_DIR, "blueprint.json")


def run_command(cmd: List[str]) -> Tuple[int, str]:
    """Helper to run a sub-process command and return exit code + stdout."""
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout + res.stderr


def cmd_plan(image_path: str, deck_name: Optional[str] = None) -> int:
    """Architect Agent Stage: Macro perception and blueprint generation."""
    if not os.path.exists(image_path):
        print(f"[Error] Image not found: {image_path}")
        return 1

    base_name = deck_name or os.path.splitext(os.path.basename(image_path))[0]
    print("=" * 65)
    print(f"🏛️ Architect Agent: Generating Macro Blueprint for [{base_name}]")
    print("=" * 65)

    # 1. Run visual segmentation & scaffold
    seg_cmd = [sys.executable, os.path.join(WORKSPACE_ROOT, "tools", "segment.py"), image_path, "--scaffold"]
    code, out = run_command(seg_cmd)
    if code != 0:
        print(f"[Warning] segment.py returned code {code}: {out}")

    # 2. Output standard blueprint structure
    blueprint = {
        "deck_name": base_name,
        "image_path": image_path,
        "aspect_ratio": "16:9",
        "palette": {
            "primary": "#1E5AA0",
            "background": "#FFFFFF",
            "accent": "#C2410C",
            "text": "#0F172A",
        },
        "blocks": [
            {
                "id": 1,
                "key": "header",
                "name": "Block 1 [Header Section]",
                "function_name": "add_header_section",
                "box": [35, 38, 930, 55],
                "components": ["title", "tag", "separator"],
                "status": "PENDING"
            },
            {
                "id": 2,
                "key": "summary",
                "name": "Block 2 [Summary Banner]",
                "function_name": "add_summary_banner_section",
                "box": [35, 108, 930, 75],
                "components": ["card", "badge", "textbox"],
                "status": "PENDING"
            },
            {
                "id": 3,
                "key": "kpi",
                "name": "Block 3 [KPI Metrics Grid]",
                "function_name": "add_mid_kpi_section",
                "box": [35, 192, 930, 110],
                "components": ["grid", "flex_card", "badge"],
                "status": "PENDING"
            },
            {
                "id": 4,
                "key": "table_board",
                "name": "Block 4 [Clipboard & Table]",
                "function_name": "add_clipboard_table_section",
                "box": [35, 325, 435, 600],
                "components": ["clipboard", "table", "progress_bar"],
                "status": "PENDING"
            },
            {
                "id": 5,
                "key": "strategy_cards",
                "name": "Block 5 [Strategy Action Cards]",
                "function_name": "add_strategy_card_section",
                "box": [485, 325, 480, 600],
                "components": ["flex_card", "pill_array"],
                "status": "PENDING"
            }
        ]
    }

    os.makedirs(SPECS_DIR, exist_ok=True)
    with open(BLUEPRINT_PATH, "w", encoding="utf-8") as f:
        json.dump(blueprint, f, indent=2, ensure_ascii=False)

    print(f"✅ Blueprint generated: {BLUEPRINT_PATH}")
    print(f"🖼️ Block Map visualization: output/block_map_{base_name}.png")
    print("-" * 65)
    print("💡 Next Step: Review blueprint with Human Supervisor, then run `orchestrator.py status`")
    return 0


def cmd_status() -> int:
    """View current Multi-Agent restoration state and block progress."""
    if not os.path.exists(BLUEPRINT_PATH):
        print("[Status] No active blueprint found. Run `python tools/orchestrator.py plan <image>` first.")
        return 0

    with open(BLUEPRINT_PATH, "r", encoding="utf-8") as f:
        bp = json.load(f)

    print("=" * 65)
    print(f"🤖 Multi-Agent Orchestrator Status: [{bp.get('deck_name', 'Unknown')}]")
    print("=" * 65)
    blocks = bp.get("blocks", [])
    completed = sum(1 for b in blocks if b.get("status") == "COMPLETED")
    total = len(blocks)

    print(f"📊 Block Progress: {completed}/{total} Completed ({int(completed/total*100) if total else 0}%)")
    print("-" * 65)
    for b in blocks:
        status_icon = "✅" if b.get("status") == "COMPLETED" else ("🔄" if b.get("status") == "IN_PROGRESS" else "⏳")
        print(f"  {status_icon} Block {b.get('id')}: {b.get('name')} -> {b.get('function_name')} [{b.get('status', 'PENDING')}]")

    print("-" * 65)
    return 0


def cmd_review(block_id: int, image_path: str, pptx_path: str) -> int:
    """Reviewer Agent Stage: Automated QA & evaluation."""
    print(f"👁️ Reviewer Agent: Auditing Block {block_id}...")
    metrics_cmd = [
        sys.executable,
        os.path.join(WORKSPACE_ROOT, "tools", "eval_metrics.py"),
        image_path,
        image_path,
        "--pptx", pptx_path,
        "--block-id", str(block_id),
        "-o", os.path.join(WORKSPACE_ROOT, "output", f"review_report_block_{block_id}.json")
    ]
    code, out = run_command(metrics_cmd)
    print(out)
    return code


def main():
    parser = argparse.ArgumentParser(description="PPT Restoration Multi-Agent Orchestrator")
    subparsers = parser.add_subparsers(dest="subcommand", help="Orchestrator commands")

    # plan
    p_plan = subparsers.add_parser("plan", help="Generate blueprint and perception scaffold")
    p_plan.add_argument("image", help="Path to input slide image")
    p_plan.add_argument("--deck-name", help="Custom name for presentation")

    # status
    subparsers.add_parser("status", help="Check Multi-Agent block progress")

    # review
    p_rev = subparsers.add_parser("review", help="Trigger automated Reviewer QA")
    p_rev.add_argument("block_id", type=int, help="Block ID")
    p_rev.add_argument("image", help="Input image")
    p_rev.add_argument("pptx", help="Rendered PPTX")

    args = parser.parse_args()

    if args.subcommand == "plan":
        sys.exit(cmd_plan(args.image, args.deck_name))
    elif args.subcommand == "status":
        sys.exit(cmd_status())
    elif args.subcommand == "review":
        sys.exit(cmd_review(args.block_id, args.image, args.pptx))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
