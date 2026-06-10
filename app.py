"""Language Transfer Map — Streamlit app."""

import json
import streamlit as st
from pathlib import Path

from core import (
    LANGUAGE_ISO, compute_ease, load_bundle,
    _bottleneck, _best_sources, compute_script_access,
)
from graph import build_graph_html, FAMILY_MAP

BUNDLE_DIR = Path(__file__).parent / "data" / "app_bundle"
ASSETS_DIR = Path(__file__).parent / "assets"

st.set_page_config(
    page_title="Language Transfer Map",
    page_icon="\U0001F30D",
    layout="wide",
)


@st.cache_resource
def get_bundle():
    return load_bundle(BUNDLE_DIR)


@st.cache_resource
def get_pair_sims():
    return json.loads((BUNDLE_DIR / "pairwise_sims.json").read_text(encoding="utf-8"))


ALL_LANGUAGES = sorted(
    [n for n in LANGUAGE_ISO if n != "Mandarin"],
    key=str.casefold,
)

PROFICIENCY_GUIDE = (ASSETS_DIR / "proficiency-levels.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Sidebar — portfolio input
# ---------------------------------------------------------------------------

@st.dialog("Proficiency scale reference", width="large")
def _show_proficiency_guide():
    _, col, _ = st.columns([1, 3, 1])
    with col:
        st.markdown(PROFICIENCY_GUIDE, unsafe_allow_html=False)


st.sidebar.title("Your Language Portfolio")

if st.sidebar.button("Proficiency scale reference"):
    _show_proficiency_guide()

st.sidebar.caption(
    "Tip: use an AI chatbot with the "
    "[assessment method](https://github.com/akmalayari/language-transfer-map/blob/main/assets/assessment-method.md) "
    "to get a precise level for each language."
)

selected_languages = st.sidebar.multiselect(
    "Select your languages",
    options=ALL_LANGUAGES,
    default=["English"],
)

portfolio: dict[str, int] = {}
for lang in selected_languages:
    level = st.sidebar.slider(
        lang,
        min_value=0,
        max_value=5,
        value=3,
        key=f"level_{lang}",
    )
    portfolio[lang] = level

if not portfolio or all(v == 0 for v in portfolio.values()):
    st.title("Language Transfer Map")
    st.info("Add languages to your portfolio in the sidebar and set at least one to level 1+.")
    st.stop()


# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------

bundle = get_bundle()
pair_sims = get_pair_sims()

portfolio_key = tuple(sorted(portfolio.items()))


@st.cache_data
def compute_all_ease(portfolio_key):
    pf = dict(portfolio_key)
    asjp = bundle["asjp"]
    wals = bundle["wals"]
    phoible = bundle["phoible"]
    scripts_data = bundle["scripts"]
    loanword = bundle["loanword"]
    genus_data = bundle["genus_data"]
    phoible_genus_data = bundle["phoible_genus_data"]
    cognate_sims = bundle["cognate_sims"]
    asjp_calibration = bundle["asjp_calibration"]

    cognate_isos = {iso for pair in cognate_sims for iso in pair}
    results = {}
    for name, iso in LANGUAGE_ISO.items():
        if name == "Mandarin":
            continue
        if iso not in asjp and iso not in cognate_isos:
            continue
        r = compute_ease(
            name, iso, pf, asjp, wals, phoible, scripts_data,
            loanword, genus_data, phoible_genus_data, cognate_sims,
            asjp_calibration,
        )
        results[name] = r
    return results


results = compute_all_ease(portfolio_key)


@st.cache_data
def get_graph_html(portfolio_key):
    return build_graph_html(dict(portfolio_key), bundle, pair_sims)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def make_report_md(portfolio, results, scripts_data):
    from datetime import date

    portfolio_rows = sorted(
        [r for r in results.values() if portfolio.get(r["name"], 0) > 0],
        key=lambda x: -x["ease"],
    )
    external = sorted(
        [r for r in results.values() if portfolio.get(r["name"], 0) == 0],
        key=lambda x: -x["ease"],
    )

    lines = []
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


def make_report_html(report_md: str) -> str:
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
# Tabs
# ---------------------------------------------------------------------------

st.title("Language Transfer Map")

report_md = make_report_md(portfolio, results, bundle["scripts"])
report_html = make_report_html(report_md)
html = get_graph_html(portfolio_key)

_external = sorted(
    [r for r in results.values() if portfolio.get(r["name"], 0) == 0],
    key=lambda x: -x["ease"],
)

tab_report, tab_graph, tab_download = st.tabs(["Report", "Graph", "Download"])

with tab_report:
    st.markdown(
        "This report ranks languages by ease of learning from your current portfolio, "
        "combining lexical, grammatical, phonological, and script similarity.\n\n"
        "| Dimension | Weight | What it measures |\n"
        "|-----------|--------|------------------|\n"
        "| Lexical | 45% | Shared vocabulary |\n"
        "| Grammar | 30% | Structural similarity |\n"
        "| Phonology | 15% | Fraction of target sounds already in your portfolio |\n"
        "| Script | 10% | Writing system accessibility |\n\n"
        "Higher proficiency in a known language gives a bonus : at level 5, ease is maximized. "
        "See [methodology](https://github.com/akmalayari/language-transfer-map/blob/main/assets/methodology.md) for full details."
    )

    portfolio_rows = sorted(
        [r for r in results.values() if portfolio.get(r["name"], 0) > 0],
        key=lambda x: -x["ease"],
    )
    if portfolio_rows:
        st.subheader("Portfolio")
        st.dataframe(
            [{"Language": r["name"], "Level": portfolio[r["name"]], "Ease": round(r["ease"], 3),
              "Bottleneck": _bottleneck(r)}
             for r in portfolio_rows],
            hide_index=True, use_container_width=True,
        )

    st.subheader("Top 20 easiest languages")
    st.dataframe(
        [{"#": i, "Language": r["name"], "Ease": round(r["ease"], 3),
          "Lex": round(r["lexical"], 2), "Gram": round(r["grammar"], 2),
          "Phon": round(r["phonology"], 2), "Script": round(r["script_access"], 2),
          "Lex source": r["lex_detail"][0][0] if r["lex_detail"] else "—",
          "Gram source": r["gram_detail"][0][0] if r["gram_detail"] else "—",
          "Bottleneck": _bottleneck(r)}
         for i, r in enumerate(_external[:20], 1)],
        hide_index=True, use_container_width=True,
    )

    st.subheader("10 hardest languages")
    st.dataframe(
        [{"Language": r["name"], "Ease": round(r["ease"], 3),
          "Primary barrier": f"{d[0][0]} ({d[0][1]:.2f})",
          "Secondary barrier": f"{d[1][0]} ({d[1][1]:.2f})"}
         for r in sorted(_external, key=lambda x: x["ease"])[:10]
         for d in [sorted([("Lexical", r["lexical"]), ("Grammar", r["grammar"]),
                            ("Phonology", r["phonology"]), ("Script", r["script_access"])],
                           key=lambda x: x[1])]],
        hide_index=True, use_container_width=True,
    )

    with st.expander(f"Full ranking — all {len(_external)} languages"):
        st.dataframe(
            [{"#": i, "Language": r["name"], "Ease": round(r["ease"], 3),
              "Lex": round(r["lexical"], 2), "Gram": round(r["grammar"], 2),
              "Phon": round(r["phonology"], 2), "Script": round(r["script_access"], 2),
              "Lex source": r["lex_detail"][0][0] if r["lex_detail"] else "—",
              "Gram source": r["gram_detail"][0][0] if r["gram_detail"] else "—",
              "Family": FAMILY_MAP.get(r["name"], "Other")}
             for i, r in enumerate(_external, 1)],
            hide_index=True, use_container_width=True,
        )

    _script_rows = compute_script_access(portfolio, bundle["scripts"])
    _known_s = sorted([s for s in _script_rows if s["known"]], key=lambda x: -len(x["gated"]))
    _unknown_s = sorted([s for s in _script_rows if not s["known"] and s["gated"]], key=lambda x: -len(x["gated"]))
    if _known_s or _unknown_s:
        with st.expander("Script access"):
            if _known_s:
                st.markdown("**Known scripts**")
                st.dataframe(
                    [{"Script": sr["script"], "Type": sr["type"],
                      "Known from": sr["sources"], "Languages unlocked": len(sr["gated"])}
                     for sr in _known_s],
                    hide_index=True, use_container_width=True,
                )
            if _unknown_s:
                st.markdown("**Scripts not yet known**")
                st.dataframe(
                    [{"Script": sr["script"], "Type": sr["type"],
                      "Difficulty": f"{sr['difficulty']}/5",
                      "Languages gated": len(sr["gated"])}
                     for sr in _unknown_s],
                    hide_index=True, use_container_width=True,
                )

with tab_graph:
    st.caption("Interactive force-directed graph. Hover for details, drag nodes, use controls to filter.")
    graph_height = st.slider("Height (px)", min_value=500, max_value=1000, value=600, step=50, key="graph_height")
    st.components.v1.html(html, height=graph_height, scrolling=False)

with tab_download:
    st.subheader("Download your results")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "Report (.html)",
            data=report_html,
            file_name="language-transfer-report.html",
            mime="text/html",
        )
    with col2:
        st.download_button(
            "Report (.md)",
            data=report_md,
            file_name="language-transfer-report.md",
            mime="text/markdown",
        )
    with col3:
        st.download_button(
            "Graph (.html)",
            data=html,
            file_name="language-transfer-map.html",
            mime="text/html",
        )
