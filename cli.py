"""Language Transfer Map — command-line interface."""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from core import (
    LANGUAGE_ISO, compute_ease, load_bundle,
    _bottleneck, _best_sources, compute_script_access,
)
from graph import build_graph_html, FAMILY_MAP

BUNDLE_DIR = Path(__file__).parent / "data" / "app_bundle"


# ---------------------------------------------------------------------------
# Portfolio parsing
# ---------------------------------------------------------------------------

def _parse_portfolio(s: str) -> dict[str, int]:
    portfolio: dict[str, int] = {}
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            sys.exit(f"Error: bad entry {part!r} — expected 'Language:level'")
        name, level_s = part.rsplit(":", 1)
        name = name.strip()
        try:
            level = int(level_s.strip())
        except ValueError:
            sys.exit(f"Error: level must be an integer, got {level_s.strip()!r}")
        if not 0 <= level <= 5:
            sys.exit(f"Error: level must be 0–5, got {level}")
        if name not in LANGUAGE_ISO:
            # suggest close matches
            close = [n for n in LANGUAGE_ISO if n.lower().startswith(name.lower()[:4])]
            hint = f"  Did you mean: {', '.join(close[:5])}?" if close else ""
            sys.exit(f"Error: unknown language {name!r}.{hint}")
        portfolio[name] = level
    return portfolio


# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------

def _compute_all(portfolio: dict, bundle: dict) -> dict:
    cognate_isos = {iso for pair in bundle["cognate_sims"] for iso in pair}
    results = {}
    for name, iso in LANGUAGE_ISO.items():
        if name == "Mandarin":
            continue
        if iso not in bundle["asjp"] and iso not in cognate_isos:
            continue
        r = compute_ease(
            name, iso, portfolio,
            bundle["asjp"], bundle["wals"], bundle["phoible"], bundle["scripts"],
            bundle["loanword"], bundle["genus_data"], bundle["phoible_genus_data"],
            bundle["cognate_sims"], bundle["asjp_calibration"],
        )
        results[name] = r
    return results


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _print_ranked(results: dict, portfolio: dict, top: int) -> None:
    external = sorted(
        [r for r in results.values() if portfolio.get(r["name"], 0) == 0],
        key=lambda x: -x["ease"],
    )
    header = f"{'#':>3}  {'Language':<26} {'Ease':>6}  {'Lex':>5}  {'Gram':>5}  {'Phon':>5}  {'Script':>6}  Bottleneck"
    sep = "-" * len(header)
    print(header)
    print(sep)
    for i, r in enumerate(external[:top], 1):
        print(
            f"{i:>3}  {r['name']:<26} {r['ease']:>6.3f}  {r['lexical']:>5.2f}  "
            f"{r['grammar']:>5.2f}  {r['phonology']:>5.2f}  {r['script_access']:>6.2f}  "
            f"{_bottleneck(r)}"
        )


def _print_target(name: str, results: dict, portfolio: dict) -> None:
    if name not in results:
        sys.exit(f"Error: no data for {name!r} — check the spelling or try a listed language")
    r = results[name]
    in_portfolio = portfolio.get(name, 0) > 0

    print(f"\n{name}{' (in portfolio)' if in_portfolio else ''}")
    print(f"  Ease:      {r['ease']:.3f}")
    print(f"  Lexical:   {r['lexical']:.3f}  {_best_sources(r)}")
    print(f"  Grammar:   {r['grammar']:.3f}  "
          f"{'  source: ' + r['gram_detail'][0][0] if r['gram_detail'] else ''}")
    print(f"  Phonology: {r['phonology']:.3f}  ({r['phon_new_count']} new sounds)")
    print(f"  Script:    {r['script_access']:.3f}"
          + (f"  ×{r['script_penalty']:.2f} logographic penalty" if r["script_penalty"] < 1.0 else ""))
    bn = _bottleneck(r)
    if bn != "—":
        print(f"  Bottleneck: {bn}")
    if r["lex_detail"]:
        print("\n  Lexical sources:")
        for src_name, combined, c in r["lex_detail"][:6]:
            print(f"    {src_name:<22} sim={combined:.3f}  contribution={c:.3f}")
    if r["gram_detail"]:
        print("\n  Grammar sources:")
        for src_name, sim, c in r["gram_detail"][:6]:
            print(f"    {src_name:<22} sim={sim:.3f}  contribution={c:.3f}")


# ---------------------------------------------------------------------------
# Report generation (Streamlit-free duplicates of app.py helpers)
# ---------------------------------------------------------------------------

def _make_report_md(portfolio: dict, results: dict, scripts_data: dict) -> str:
    portfolio_rows = sorted(
        [r for r in results.values() if portfolio.get(r["name"], 0) > 0],
        key=lambda x: -x["ease"],
    )
    external = sorted(
        [r for r in results.values() if portfolio.get(r["name"], 0) == 0],
        key=lambda x: -x["ease"],
    )

    lines: list[str] = []
    w = lines.append

    w("# Language Transfer Map — Ease Report")
    w("")
    w(f"*Generated {date.today()}.*")
    w("")
    w("Languages ranked by ease of learning from your current portfolio, "
      "combining lexical, grammatical, phonological, and script similarity.")
    w("")

    w("## How to read these scores")
    w("")
    w("| Dimension | Weight | What it measures |")
    w("|-----------|--------|-----------------|")
    w("| Lexical | 45% | Shared vocabulary |")
    w("| Grammar | 30% | Structural similarity |")
    w("| Phonology | 15% | Fraction of target sounds already in your portfolio |")
    w("| Script | 10% | Writing system accessibility |")
    w("")
    w("Higher proficiency in a known language gives a bonus : at level 5, ease is maximized.")
    w("")
    w("*See [methodology](https://github.com/akmalayari/language-transfer-map/blob/main/assets/methodology.md) for full details.*")
    w("")

    w("## Portfolio")
    w("")
    w("| Language | Level | Ease | Bottleneck |")
    w("|----------|-------|------|------------|")
    for r in portfolio_rows:
        w(f"| {r['name']} | {portfolio[r['name']]} | {r['ease']:.3f} | {_bottleneck(r)} |")
    w("")

    w("## Top 20 easiest languages")
    w("")
    w("| # | Language | Ease | Lex | Gram | Phon | Script | Best sources | Bottleneck |")
    w("|---|----------|------|-----|------|------|--------|--------------|------------|")
    for i, r in enumerate(external[:20], 1):
        w(f"| {i} | {r['name']} | {r['ease']:.3f} | {r['lexical']:.2f} | "
          f"{r['grammar']:.2f} | {r['phonology']:.2f} | {r['script_access']:.2f} | "
          f"{_best_sources(r)} | {_bottleneck(r)} |")
    w("")

    w("## 10 hardest languages")
    w("")
    w("| Language | Ease | Primary barrier | Secondary barrier |")
    w("|----------|------|----------------|-------------------|")
    for r in sorted(external, key=lambda x: x["ease"])[:10]:
        dims = sorted([
            ("Lexical", r["lexical"]), ("Grammar", r["grammar"]),
            ("Phonology", r["phonology"]), ("Script", r["script_access"]),
        ], key=lambda x: x[1])
        w(f"| {r['name']} | {r['ease']:.3f} | {dims[0][0]} ({dims[0][1]:.2f}) | "
          f"{dims[1][0]} ({dims[1][1]:.2f}) |")
    w("")

    w("## Full ranking")
    w("")
    w('<details markdown="1">')
    w(f"<summary>All {len(external)} languages</summary>")
    w("")
    w("| # | Language | Ease | Lex | Gram | Phon | Script | Best sources | Family |")
    w("|---|----------|------|-----|------|------|--------|--------------|--------|")
    for i, r in enumerate(external, 1):
        family = FAMILY_MAP.get(r["name"], "Other")
        w(f"| {i} | {r['name']} | {r['ease']:.3f} | {r['lexical']:.2f} | "
          f"{r['grammar']:.2f} | {r['phonology']:.2f} | {r['script_access']:.2f} | "
          f"{_best_sources(r)} | {family} |")
    w("")
    w("</details>")
    w("")

    script_rows = compute_script_access(portfolio, scripts_data)
    known_s = sorted([s for s in script_rows if s["known"]], key=lambda x: -len(x["gated"]))
    unknown_s = sorted([s for s in script_rows if not s["known"] and s["gated"]], key=lambda x: -len(x["gated"]))
    if known_s or unknown_s:
        w("## Script access")
        w("")
        if known_s:
            w("### Known scripts")
            w("| Script | Type | Known from | Languages unlocked |")
            w("|--------|------|------------|-------------------|")
            for sr in known_s:
                gated = ", ".join(sr["gated"][:8])
                if len(sr["gated"]) > 8:
                    gated += f", +{len(sr['gated']) - 8} more"
                w(f"| {sr['script']} | {sr['type']} | {sr['sources']} | {gated or '—'} |")
            w("")
        if unknown_s:
            w("### Scripts not yet known")
            w("| Script | Type | Difficulty | Languages gated |")
            w("|--------|------|-----------|-----------------|")
            for sr in unknown_s:
                gated = ", ".join(sr["gated"][:6])
                if len(sr["gated"]) > 6:
                    gated += f", +{len(sr['gated']) - 6} more"
                w(f"| {sr['script']} | {sr['type']} | {sr['difficulty']}/5 | {gated} |")
            w("")

    return "\n".join(lines)


def _make_report_html(report_md: str) -> str:
    import markdown as md_lib
    body = md_lib.markdown(report_md, extensions=["tables", "md_in_html"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Language Transfer Map — Ease Report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         max-width: 860px; margin: 40px auto; padding: 0 24px;
         color: #1a1a2e; line-height: 1.6; background: #fff; }}
  h1 {{ font-size: 1.8rem; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; margin-bottom: 4px; }}
  h2 {{ font-size: 1.3rem; margin-top: 2rem; color: #2c3e50;
        border-bottom: 1px solid #eee; padding-bottom: 4px; }}
  h3 {{ font-size: 1.1rem; margin-top: 1.5rem; color: #34495e; }}
  p {{ margin: 8px 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 0.9rem; }}
  th {{ background: #f0f4f8; text-align: left; padding: 8px 12px;
        border: 1px solid #d0d7de; font-weight: 600; white-space: nowrap; }}
  td {{ padding: 7px 12px; border: 1px solid #d0d7de; }}
  tr:nth-child(even) td {{ background: #f9fafb; }}
  code {{ background: #f0f4f8; padding: 2px 5px; border-radius: 3px; font-size: 0.88em; }}
  a {{ color: #2563eb; }}
  details {{ margin: 16px 0; border: 1px solid #e0e0e0; border-radius: 6px; padding: 8px 14px; }}
  summary {{ cursor: pointer; font-weight: 600; padding: 4px 0; color: #2c3e50; user-select: none; }}
  summary:hover {{ color: #2563eb; }}
  em {{ color: #555; }}
  @media print {{
    details {{ display: block; }}
    details > * {{ display: block !important; }}
    summary {{ display: none; }}
  }}
</style>
</head>
<body>
{body}
<script>
window.addEventListener('beforeprint', () =>
    document.querySelectorAll('details').forEach(d => d.open = true));
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Language Transfer Map — generate ease reports from the command line.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  python cli.py --portfolio "French:5,Spanish:3"
  python cli.py --portfolio "French:5,Spanish:3" --top 10
  python cli.py --portfolio "French:5,Spanish:3" --target Italian
  python cli.py --portfolio "French:5,Spanish:3" --report report.html --graph
  python cli.py --portfolio "French:5,Spanish:3" --report report.md --graph map.html
""",
    )
    parser.add_argument(
        "--portfolio", required=True, metavar="STR",
        help='Your languages and levels, e.g. "French:5,Spanish:3,Russian:2"',
    )
    parser.add_argument(
        "--top", type=int, default=20, metavar="N",
        help="Rows in stdout ranked output (default: 20)",
    )
    parser.add_argument(
        "--report", nargs="?", const="language-transfer-report.md", metavar="FILE",
        help="Save report to FILE (.md or .html inferred from extension; "
             "default filename: language-transfer-report.md)",
    )
    parser.add_argument(
        "--graph", nargs="?", const="language-transfer-map.html", metavar="FILE",
        help="Save force-directed graph HTML to FILE "
             "(default filename: language-transfer-map.html)",
    )
    parser.add_argument(
        "--target", metavar="LANGUAGE",
        help="Print dimension breakdown for a specific target language",
    )
    args = parser.parse_args()

    portfolio = _parse_portfolio(args.portfolio)
    if not portfolio or all(v == 0 for v in portfolio.values()):
        sys.exit("Error: portfolio must contain at least one language with level > 0")

    print("Loading bundle…", file=sys.stderr)
    bundle = load_bundle(BUNDLE_DIR)
    pair_sims = json.loads((BUNDLE_DIR / "pairwise_sims.json").read_text(encoding="utf-8"))

    print("Computing ease scores…", file=sys.stderr)
    results = _compute_all(portfolio, bundle)

    # --target: dimension breakdown
    if args.target:
        _print_target(args.target, results, portfolio)

    # --report: save file
    if args.report:
        report_md = _make_report_md(portfolio, results, bundle["scripts"])
        ext = Path(args.report).suffix.lower()
        if ext == ".html":
            content = _make_report_html(report_md)
            fmt = "HTML"
        else:
            content = report_md
            fmt = "Markdown"
        Path(args.report).write_text(content, encoding="utf-8")
        print(f"Report ({fmt}) → {args.report}", file=sys.stderr)

    # --graph: save file
    if args.graph:
        print("Building graph…", file=sys.stderr)
        graph_html = build_graph_html(portfolio, bundle, pair_sims)
        Path(args.graph).write_text(graph_html, encoding="utf-8")
        print(f"Graph → {args.graph}", file=sys.stderr)

    # default: print ranked list to stdout when no other output was requested
    if not args.target and not args.report and not args.graph:
        _print_ranked(results, portfolio, args.top)


if __name__ == "__main__":
    main()
