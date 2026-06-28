"""Interactive D3.js force-directed language transfer map.

Public API
----------
build_graph_data(portfolio, bundle, pair_sims) -> dict
build_graph_html(portfolio, bundle, pair_sims, *, out_path=None) -> str
"""

import json
from collections import defaultdict
from pathlib import Path

from core import LANGUAGE_ISO, compute_ease

# ---------------------------------------------------------------------------
# Display constants (graph-specific, not core compute)
# ---------------------------------------------------------------------------

FAMILY_MAP = {
    # Romance
    "French": "Italic", "Spanish": "Italic", "Portuguese": "Italic",
    "Italian": "Italic", "Romanian": "Italic", "Catalan": "Italic",
    "Galician": "Italic", "Occitan": "Italic", "Latin": "Italic",
    "Sardinian": "Italic",
    # Germanic
    "English": "Germanic", "German": "Germanic", "Dutch": "Germanic",
    "Swedish": "Germanic", "Norwegian": "Germanic", "Danish": "Germanic",
    "Icelandic": "Germanic", "Faroese": "Germanic",
    "Afrikaans": "Germanic", "Luxembourgish": "Germanic",
    "Yiddish": "Germanic",
    # Celtic
    "Breton": "Celtic", "Welsh": "Celtic", "Irish": "Celtic",
    "Scottish Gaelic": "Celtic",
    # Slavic
    "Russian": "Slavic", "Ukrainian": "Slavic", "Bulgarian": "Slavic",
    "Macedonian": "Slavic", "Serbian": "Slavic", "Croatian": "Slavic",
    "Bosnian": "Slavic", "Slovenian": "Slavic", "Polish": "Slavic",
    "Czech": "Slavic", "Slovak": "Slavic", "Belarusian": "Slavic",
    # Baltic
    "Lithuanian": "Baltic", "Latvian": "Baltic",
    # Hellenic
    "Greek": "Hellenic",
    # Albanian
    "Albanian": "Albanian",
    # Armenian
    "Armenian": "Armenian",
    # Indo-Iranian
    "Hindi": "Indo-Iranian", "Nepali": "Indo-Iranian", "Marathi": "Indo-Iranian",
    "Sanskrit": "Indo-Iranian", "Urdu": "Indo-Iranian", "Persian": "Indo-Iranian",
    "Pashto": "Indo-Iranian", "Bengali": "Indo-Iranian", "Assamese": "Indo-Iranian",
    "Punjabi": "Indo-Iranian", "Gujarati": "Indo-Iranian", "Sinhala": "Indo-Iranian",
    "Kurdish": "Indo-Iranian",
    # Dravidian
    "Tamil": "Dravidian", "Telugu": "Dravidian", "Kannada": "Dravidian",
    "Malayalam": "Dravidian",
    # Semitic
    "Standard Arabic": "Semitic", "Tunisian Arabic": "Semitic",
    "Egyptian Arabic": "Semitic", "Levantine Arabic": "Semitic",
    "Moroccan Arabic": "Semitic", "Gulf Arabic": "Semitic",
    "Hebrew": "Semitic", "Amharic": "Semitic", "Tigrinya": "Semitic", "Maltese": "Semitic",
    # Turkic
    "Turkish": "Turkic", "Azerbaijani (N.)": "Turkic", "Azerbaijani (S.)": "Turkic", "Uzbek": "Turkic",
    "Kazakh": "Turkic", "Kyrgyz": "Turkic", "Tatar": "Turkic",
    "Uyghur": "Turkic", "Turkmen": "Turkic", "Bashkir": "Turkic",
    "Yakut": "Turkic",
    # Mongolic
    "Mongolian": "Mongolic",
    # Koreanic
    "Korean": "Koreanic", "Middle Korean": "Koreanic",
    # Japonic
    "Japanese": "Japonic", "Okinawan": "Japonic",
    # Sino-Tibetan
    "Chinese": "Sino-Tibetan", "Mandarin": "Sino-Tibetan",
    "Cantonese": "Sino-Tibetan", "Wu": "Sino-Tibetan", "Hakka": "Sino-Tibetan",
    "Min Nan": "Sino-Tibetan", "Tibetan": "Sino-Tibetan", "Burmese": "Sino-Tibetan",
    # Austronesian
    "Indonesian": "Austronesian", "Malay": "Austronesian", "Tagalog": "Austronesian",
    "Javanese": "Austronesian", "Malagasy": "Austronesian",
    # Tai-Kadai
    "Thai": "Tai-Kadai", "Lao": "Tai-Kadai",
    # Austroasiatic
    "Vietnamese": "Austroasiatic", "Khmer": "Austroasiatic",
    # Kartvelian
    "Georgian": "Caucasian", "Mingrelian": "Caucasian", "Laz": "Caucasian", "Svan": "Caucasian",
    # Uralic
    "Finnish": "Uralic", "Estonian": "Uralic", "Hungarian": "Uralic",
    # Niger-Congo
    "Swahili": "Niger-Congo", "Yoruba": "Niger-Congo", "Igbo": "Niger-Congo",
    "Hausa": "Niger-Congo", "Wolof": "Niger-Congo", "Zulu": "Niger-Congo",
    "Xhosa": "Niger-Congo",
    # Creole / Pidgin
    "Haitian Creole": "Creole", "Tok Pisin": "Creole",
    # Constructed
    "Esperanto": "Constructed",
    # Polynesian / Oceanic
    "Hawaiian": "Austronesian", "Maori": "Austronesian", "Samoan": "Austronesian",
    # Niger-Congo (additional)
    "Kinyarwanda": "Niger-Congo", "Shona": "Niger-Congo", "Lingala": "Niger-Congo",
    "Bambara": "Niger-Congo", "Chichewa": "Niger-Congo", "Tswana": "Niger-Congo",
    "Luganda": "Niger-Congo",
    # Austronesian (additional)
    "Cebuano": "Austronesian", "Sundanese": "Austronesian",
    # Quechuan
    "Quechua": "Americas",
    # Caucasian (non-Kartvelian)
    "Chechen": "Caucasian", "Avar": "Caucasian", "Abkhaz": "Caucasian",
    "Adyghe": "Caucasian", "Kabardian": "Caucasian",
    # Native American
    "Navajo": "Americas", "Cherokee": "Americas", "Nahuatl": "Americas",
    "Mapuche": "Americas", "Yupik": "Americas", "St Lawrence Yupik": "Americas",
    "Inuktitut": "Americas", "Kalaallisut": "Americas", "Kiche": "Americas",
    "Yucatec Maya": "Americas",
    # Siberian / Paleosiberian
    "Evenki": "Paleosiberian", "Chukchi": "Paleosiberian", "Koryak": "Paleosiberian",
    "Ainu": "Paleosiberian", "Ket": "Paleosiberian", "Nivkh": "Paleosiberian",
    # Tungusic
    "Manchu": "Tungusic", "Even": "Tungusic", "Nanai": "Tungusic",
    # Turkic (extended)
    "Chuvash": "Turkic", "Gagauz": "Turkic", "Tuvan": "Turkic", "Khakas": "Turkic",
    # Mongolic (extended)
    "Buryat": "Mongolic",
    # Uralic (extended)
    "North Saami": "Uralic", "Erzya": "Uralic", "Komi": "Uralic",
    "Udmurt": "Uralic", "Mari": "Uralic",
    # Dravidian (extended)
    "Brahui": "Dravidian",
    # Austronesian (Oceanic)
    "Tongan": "Austronesian", "Fijian": "Austronesian",
    # Paleoeuropean
    "Basque": "Paleoeuropean",
    # Cushitic
    "Somali": "Cushitic",
    # IE living (new)
    "Bhojpuri": "Indo-Iranian", "Kashmiri": "Indo-Iranian", "Maithili": "Indo-Iranian",
    "Ossetic": "Indo-Iranian", "Western Armenian": "Armenian",
    # IE historical — Germanic
    "Gothic": "Germanic", "Old Norse": "Germanic", "Old High German": "Germanic",
    "Old English": "Germanic", "Middle High German": "Germanic", "Middle Dutch": "Germanic",
    # IE historical — Celtic
    "Cornish": "Celtic", "Old Irish": "Celtic",
    "Middle Welsh": "Celtic", "Middle Breton": "Celtic", "Gaulish": "Celtic",
    # IE historical — Romance / Italic
    "Anglo-Norman": "Italic", "Old Spanish": "Italic", "Oscan": "Italic", "Umbrian": "Italic",
    # IE historical — Hellenic
    "Ancient Greek": "Hellenic", "Mycenaean Greek": "Hellenic",
    # IE historical — Armenian
    "Classical Armenian": "Armenian",
    # IE historical — Indo-Iranian
    "Pali": "Indo-Iranian", "Middle Persian": "Indo-Iranian",
    "Sogdian": "Indo-Iranian", "Old Persian": "Indo-Iranian",
    "Hittite": "Anatolian",
    "Tocharian A": "Tocharian", "Tocharian B": "Tocharian",
    # IE historical — Slavic / Baltic
    "Old Novgorod": "Slavic", "Rusyn": "Slavic",
    "Old Prussian": "Baltic",
    # Austronesian (new)
    "Hiligaynon": "Austronesian", "Minangkabau": "Austronesian", "Acehnese": "Austronesian",
    "Kapampangan": "Austronesian", "Iban": "Austronesian", "Toba Batak": "Austronesian",
    "Tahitian": "Austronesian", "Tausug": "Austronesian", "Paiwan": "Austronesian",
    # Bantu (new)
    "Kikuyu": "Niger-Congo", "Kikongo": "Niger-Congo", "Rukiga": "Niger-Congo",
    "Ndebele": "Niger-Congo", "Runyankore": "Niger-Congo",
    # Sino-Tibetan (new)
    "Garo": "Sino-Tibetan", "Mizo": "Sino-Tibetan", "Lisu": "Sino-Tibetan",
    "Chin Hakha": "Sino-Tibetan",
    "Old Chinese": "Sino-Tibetan", "Old Tibetan": "Sino-Tibetan", "Old Burmese": "Sino-Tibetan",
    # Japonic historical
    "Old Japanese": "Japonic",
    # Austroasiatic (new)
    "Mon": "Austroasiatic", "Mundari": "Austroasiatic", "Khasi": "Austroasiatic",
    # Americas (new)
    "Guaraní": "Americas",
    "Imbabura Quechua": "Americas",
    "Kaqchikel": "Americas", "Mam": "Americas", "Tzotzil": "Americas",
    "Q'eqchi'": "Americas", "Tzeltal": "Americas", "Huastec": "Americas",
    # Semitic (new)
    "Tigre": "Semitic", "Ge'ez": "Semitic",
    "Iraqi Arabic": "Semitic", "Yemeni Arabic": "Semitic", "Chadian Arabic": "Semitic",
    # Semitic ancient (ASJP only)
    "Akkadian": "Semitic", "Phoenician": "Semitic", "Ugaritic": "Semitic",
    "Classical Syriac": "Semitic", "Coptic": "Semitic",
    # Dravidian (new)
    "Tulu": "Dravidian",
    # Turkic historical
    "Old Turkic": "Turkic",
    # Paleoeuropean (continued)
    "Etruscan": "Paleoeuropean",
    # Ancient Mesopotamian
    "Sumerian": "Ancient Mesopotamian", "Elamite": "Ancient Mesopotamian",
    # Berber
    "Tamazight": "Berber", "Kabyle": "Berber", "Tachelhit": "Berber",
    # Nilo-Saharan
    "Kanuri": "Nilo-Saharan", "Luo": "Nilo-Saharan",
    # Khoisan
    "Khoekhoe": "Khoisan",
    # Hmong-Mien
    "Hmong": "Hmong-Mien",
    # Gbe
    "Ewe": "Niger-Congo", "Fon": "Niger-Congo",
    # Algonquian + Siouan
    "Cree": "Americas", "Lakota": "Americas",
    # Cushitic (Beja genus)
    "Beja": "Cushitic",
    # Isolates
    "Burushaski": "Isolate", "Tlingit": "Americas",
    # NE Caucasian (additional)
    "Lezgi": "Caucasian", "Ingush": "Caucasian", "Lak": "Caucasian", "Dargi": "Caucasian",
    # Uralic — Samoyedic
    "Nenets": "Uralic", "Nganasan": "Uralic", "Selkup": "Uralic", "Kamas": "Uralic",
    # Yukaghir
    "Yukaghir": "Paleosiberian", "Kolyma Yukaghir": "Paleosiberian",
    # Mongolic (extended)
    "Kalmyk": "Mongolic",
    # Ugric (extended)
    "Khanty": "Uralic", "Mansi": "Uralic",
    # Iranian (extended)
    "Kurmanji": "Indo-Iranian",
    # Northwest Caucasian — historical
    "Ubykh": "Caucasian",
    # Saami (extended)
    "Southern Saami": "Uralic", "Kildin Saami": "Uralic",
    # Aymaran
    "Aymara": "Americas",
}

FAMILY_COLORS = {
    "Italic":       "#e74c3c",
    "Germanic":      "#3498db",
    "Slavic":        "#2ecc71",
    "Celtic":        "#9b59b6",
    "Baltic":        "#1abc9c",
    "Hellenic":      "#e67e22",
    "Albanian":      "#f39c12",
    "Armenian":      "#d35400",
    "Anatolian":     "#8b5e3c",
    "Tocharian":     "#5c6bc0",
    "Indo-Iranian":  "#e91e63",
    "Dravidian":     "#ff5722",
    "Semitic":       "#ffc107",
    "Turkic":        "#795548",
    "Mongolic":      "#8d6e63",
    "Koreanic":      "#607d8b",
    "Japonic":       "#f06292",
    "Sino-Tibetan":  "#c62828",
    "Austronesian":  "#00bcd4",
    "Tai-Kadai":     "#8bc34a",
    "Austroasiatic":  "#cddc39",
    "Uralic":        "#3f51b5",
    "Niger-Congo":   "#ff9800",
    "Paleoeuropean":        "#a0785a",
    "Ancient Mesopotamian": "#c4a35a",
    "Cushitic":      "#bcaaa4",
    "Berber":        "#a67c52",
    "Nilo-Saharan":  "#ff8f00",
    "Khoisan":       "#26a69a",
    "Hmong-Mien":    "#7cb342",
    "Isolate":       "#9e9e9e",
    "Creole":        "#4dd0e1",
    "Constructed":   "#b0bec5",
    "Caucasian":       "#5d4037",
    "Americas":        "#7e57c2",
    "Paleosiberian":   "#78909c",
    "Tungusic":        "#546e7a",
}

FAMILY_ANGLES = {
    "Italic":       0.0,
    "Constructed":   0.2,
    "Creole":       -0.25,
    "Germanic":      0.4,
    "Celtic":        0.6,
    "Hellenic":      0.75,
    "Albanian":      0.9,
    "Slavic":        1.05,
    "Baltic":        1.2,
    "Armenian":      1.35,
    "Anatolian":     1.45,
    "Caucasian":     1.55,
    "Uralic":        1.7,
    "Turkic":        1.85,
    "Mongolic":      2.1,
    "Tocharian":     2.22,
    "Indo-Iranian":  2.35,
    "Isolate":       2.5,
    "Dravidian":     2.65,
    "Americas":      2.85,
    "Paleoeuropean":        -0.4,
    "Ancient Mesopotamian": -0.62,
    "Semitic":      -0.85,
    "Cushitic":     -1.1,
    "Berber":       -1.22,
    "Niger-Congo":  -1.35,
    "Nilo-Saharan": -1.44,
    "Khoisan":      -1.52,
    "Koreanic":     -1.6,
    "Japonic":      -1.8,
    "Austroasiatic":-2.0,
    "Hmong-Mien":   -2.1,
    "Tai-Kadai":    -2.2,
    "Tungusic":     -2.33,
    "Paleosiberian":-2.45,
    "Sino-Tibetan": -2.65,
    "Austronesian": -2.9,
}

_HISTORICAL_NAMES = frozenset({
    "Latin", "Gothic", "Gaulish", "Oscan", "Umbrian", "Cornish",
    "Pali", "Hittite", "Anglo-Norman", "Sogdian",
    "Tocharian A", "Tocharian B", "Mycenaean Greek",
    "Sanskrit",
    "Ge'ez", "Akkadian", "Phoenician", "Ugaritic", "Coptic",
    "Sumerian", "Elamite", "Etruscan",
    "Ubykh", "Kamas",
})
_HISTORICAL_PREFIXES = ("Old ", "Middle ", "Ancient ", "Classical ", "Proto-")


def _is_historical(name: str) -> bool:
    return name in _HISTORICAL_NAMES or any(name.startswith(p) for p in _HISTORICAL_PREFIXES)


# ---------------------------------------------------------------------------
# Core graph builder
# ---------------------------------------------------------------------------

def build_graph_data(
    portfolio: dict[str, float],
    bundle: dict,
    pair_sims: dict[str, float],
) -> dict:
    """Compute graph data: nodes, links, and metadata.

    Parameters
    ----------
    portfolio : {language_name: level}
    bundle    : dict from core.load_bundle()
    pair_sims : pre-computed dict from pairwise_sims.json
                Keys are "name1|||name2" (canonical sorted order).
    """
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
    all_results = {}
    for name, iso in LANGUAGE_ISO.items():
        if name == "Mandarin":
            continue
        if iso not in asjp and iso not in cognate_isos:
            continue
        r = compute_ease(
            name, iso, portfolio, asjp, wals, phoible, scripts_data,
            loanword, genus_data, phoible_genus_data, cognate_sims,
            asjp_calibration,
        )
        all_results[name] = r

    included_list = sorted(set(portfolio.keys()) | set(all_results.keys()))

    def _lookup_pair_sim(n1: str, n2: str) -> float:
        k = f"{n1}|||{n2}"
        v = pair_sims.get(k)
        if v is not None:
            return v
        return pair_sims.get(f"{n2}|||{n1}", 0.0)

    # Same-ISO groups (e.g. Serbian/Croatian/Bosnian -> hbs)
    iso_groups: dict[str, list[str]] = defaultdict(list)
    for name in included_list:
        iso = LANGUAGE_ISO.get(name)
        if iso:
            iso_groups[iso].append(name)

    def top_similar(name, k=6):
        neighbors = []
        for n2 in included_list:
            if n2 == name:
                continue
            sim = _lookup_pair_sim(name, n2)
            # Override for same-ISO pairs
            iso1 = LANGUAGE_ISO.get(name)
            iso2 = LANGUAGE_ISO.get(n2)
            if iso1 and iso2 and iso1 == iso2:
                sim = 0.98
            if sim > 0:
                neighbors.append((n2, sim))
        neighbors.sort(key=lambda x: -x[1])
        return [
            {"name": n, "sim": round(s, 3), "historical": _is_historical(n)}
            for n, s in neighbors[:k]
        ]

    nodes = []

    for name, level in portfolio.items():
        if level == 0:
            continue
        iso = LANGUAGE_ISO.get(name, "")
        family = FAMILY_MAP.get(name, "Other")
        r = all_results.get(name)
        node = {
            "id": name, "iso": iso, "level": level, "family": family,
            "type": "portfolio", "radius": max(8, 6 + level * 4),
            "historical": _is_historical(name),
        }
        if r:
            node.update({
                "ease": round(r["ease"], 3),
                "transfer_ease": round(r["transfer_ease"], 3),
                "proficiency": round(r["proficiency"], 2),
                "lex": round(r["lexical"], 3),
                "gram": round(r["grammar"], 3),
                "phon": round(r["phonology"], 3),
                "script": round(r["script_access"], 3),
                "penalty": round(r["script_penalty"], 2),
                "top_sources": top_similar(name),
            })
        else:
            node.update({
                "ease": None, "transfer_ease": None, "proficiency": None,
                "lex": None, "gram": None, "phon": None,
                "script": None, "penalty": None, "top_sources": [],
            })
        nodes.append(node)

    for name, r in all_results.items():
        if name in portfolio and portfolio[name] > 0:
            continue
        family = FAMILY_MAP.get(name, "Other")
        nodes.append({
            "id": name, "iso": r["iso"], "level": None, "family": family,
            "type": "target", "radius": 6, "historical": _is_historical(name),
            "ease": round(r["ease"], 3),
            "transfer_ease": round(r["transfer_ease"], 3),
            "proficiency": round(r["proficiency"], 2),
            "lex": round(r["lexical"], 3),
            "gram": round(r["grammar"], 3),
            "phon": round(r["phonology"], 3),
            "script": round(r["script_access"], 3),
            "penalty": round(r["script_penalty"], 2),
            "top_sources": top_similar(name),
        })

    # Build links from pair_sims (floor 0.20)
    node_names = {n["id"] for n in nodes}
    links = []
    seen = set()
    for key, sim in pair_sims.items():
        if sim < 0.20:
            continue
        parts = key.split("|||")
        if len(parts) != 2:
            continue
        n1, n2 = parts
        if n1 not in node_names or n2 not in node_names:
            continue
        canon = tuple(sorted([n1, n2]))
        if canon in seen:
            continue
        seen.add(canon)
        is_portfolio_link = portfolio.get(n1, 0) > 0 and portfolio.get(n2, 0) > 0
        links.append({
            "source": n1, "target": n2,
            "weight": round(sim, 3),
            "type": "portfolio" if is_portfolio_link else "transfer",
        })

    # Same-ISO links
    for names in iso_groups.values():
        if len(names) > 1:
            for i, n1 in enumerate(names):
                if n1 not in node_names:
                    continue
                for n2 in names[i + 1:]:
                    if n2 not in node_names:
                        continue
                    canon = tuple(sorted([n1, n2]))
                    if canon in seen:
                        continue
                    seen.add(canon)
                    is_portfolio_link = portfolio.get(n1, 0) > 0 and portfolio.get(n2, 0) > 0
                    links.append({
                        "source": n1, "target": n2,
                        "weight": 0.98,
                        "type": "portfolio" if is_portfolio_link else "transfer",
                    })

    return {
        "nodes": nodes,
        "links": links,
        "familyColors": FAMILY_COLORS,
        "familyAngles": {f: round(a, 3) for f, a in FAMILY_ANGLES.items()},
    }


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Language Transfer Map</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0d1117; color: #c9d1d9; font-family: -apple-system, system-ui, sans-serif; overflow: hidden; }
#graph { width: 100vw; height: 100vh; }

.link-portfolio { stroke-opacity: 0.15; }
.link-transfer { stroke-opacity: 0.25; stroke-dasharray: 4 2; }
.link-highlight { stroke-opacity: 0.8 !important; }

.node-portfolio { stroke-width: 2; cursor: pointer; }
.node-target { stroke-width: 1.5; fill-opacity: 0.7; cursor: pointer; }
.node-highlight { stroke: #fff !important; stroke-width: 3 !important; }
.node-dim { opacity: 0.15; }
.link-dim { opacity: 0.05; }

.label { font-size: 11px; fill: #c9d1d9; pointer-events: none; text-anchor: middle; }
.label-portfolio { font-weight: 600; font-size: 12px; }
.label-dim { opacity: 0.1; }

#tooltip {
    position: absolute; pointer-events: none; display: none;
    background: #161b22; border: 1px solid #30363d; border-radius: 8px;
    padding: 12px 16px; font-size: 13px; line-height: 1.6;
    max-width: 320px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); z-index: 100;
}
#tooltip h3 { font-size: 15px; margin-bottom: 4px; }
#tooltip .family-tag { font-size: 11px; padding: 2px 6px; border-radius: 4px; color: #fff; }
#tooltip .dim { display: flex; justify-content: space-between; }
#tooltip .dim-label { color: #8b949e; }
#tooltip .dim-bar { display: inline-block; height: 10px; border-radius: 2px; margin-left: 8px; vertical-align: middle; }
#tooltip .sources { margin-top: 6px; font-size: 12px; color: #8b949e; }

#family-panel {
    position: absolute; top: 16px; left: 16px;
    background: #161b22cc; border: 1px solid #30363d; border-radius: 8px;
    padding: 10px; font-size: 12px; width: 220px;
}
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.panel-header h3 { font-size: 14px; }
.ghost-btn {
    font-size: 11px; background: #21262d; border: 1px solid #30363d;
    color: #8b949e; padding: 2px 7px; border-radius: 4px; cursor: pointer;
}
.ghost-btn:hover { background: #30363d; color: #c9d1d9; }

#family-buttons { display: flex; flex-wrap: wrap; gap: 2px; }
.family-btn {
    display: inline-flex; align-items: center;
    padding: 2px 6px; border-radius: 10px; cursor: pointer;
    font-size: 11px; border: 1px solid; opacity: 0.4;
    transition: opacity 0.15s; user-select: none;
}
.family-btn:hover { opacity: 0.75; }
.family-btn.active { opacity: 1.0; }
.family-dot { width: 6px; height: 6px; border-radius: 50%; margin-right: 3px; flex-shrink: 0; }

.panel-divider { border-top: 1px solid #30363d; margin: 8px 0 6px; }
.toggle-row { display: flex; gap: 12px; }
.toggle-row label { display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: 12px; }

#controls {
    position: absolute; top: 16px; right: 16px;
    background: #161b22cc; border: 1px solid #30363d; border-radius: 8px;
    padding: 12px 14px; font-size: 13px;
}
#controls label { display: block; margin: 5px 0; white-space: nowrap; }
#controls input[type=range] { width: 110px; vertical-align: middle; }
#controls .val { display: inline-block; width: 32px; text-align: right; color: #8b949e; font-size: 12px; }
.action-btn {
    display: block; width: 100%; margin-top: 10px;
    background: #21262d; border: 1px solid #30363d; color: #c9d1d9;
    padding: 5px 8px; border-radius: 4px; cursor: pointer; font-size: 12px; text-align: center;
}
.action-btn:hover { background: #30363d; }

#title-bar {
    position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);
    background: #161b22cc; border: 1px solid #30363d; border-radius: 8px;
    padding: 8px 20px; font-size: 13px; text-align: center; white-space: nowrap;
}

#toggle-families, #toggle-controls {
    display: none;
    position: absolute;
    width: 36px; height: 36px;
    background: #161b22cc; border: 1px solid #30363d;
    border-radius: 8px; cursor: pointer;
    align-items: center; justify-content: center;
    font-size: 18px; color: #c9d1d9; z-index: 10;
}
#toggle-families { top: 16px; left: 16px; }
#toggle-controls { top: 16px; right: 16px; }
.panel-close {
    display: none; background: none; border: none;
    color: #8b949e; cursor: pointer; font-size: 15px; line-height: 1;
}
@media (max-width: 600px) {
    #toggle-families, #toggle-controls { display: flex; }
    #family-panel { display: none; max-height: 80vh; overflow-y: auto; z-index: 50; }
    #controls { display: none; z-index: 50; }
    #family-panel.open, #controls.open { display: block; }
    .panel-close { display: inline-block; }
}
</style>
</head>
<body>

<svg id="graph"></svg>
<div id="tooltip"></div>

<button id="toggle-families" title="Filters">&#9776;</button>
<button id="toggle-controls" title="Controls">&#9881;</button>

<div id="family-panel">
    <div class="panel-header">
        <h3>Families</h3>
        <button class="ghost-btn" id="family-reset">Show all</button>
        <button class="panel-close" id="close-families">&#x2715;</button>
    </div>
    <div id="family-buttons"></div>
    <div class="panel-divider"></div>
    <div class="toggle-row">
        <label><input type="checkbox" id="show-portfolio" checked> Portfolio</label>
        <label><input type="checkbox" id="show-targets" checked> Targets</label>
    </div>
    <div class="toggle-row">
        <label><input type="checkbox" id="show-living" checked> Living</label>
        <label><input type="checkbox" id="show-historical"> Historical</label>
    </div>
</div>

<div id="controls">
    <button class="panel-close" id="close-controls" style="float:right;margin-bottom:4px;">&#x2715;</button>
    <label>Link &ge; <input type="range" id="threshold" min="30" max="80" value="50"> <span class="val" id="threshold-val">0.50</span></label>
    <label>Ease &ge; <input type="range" id="ease-threshold" min="0" max="95" value="0"> <span class="val" id="ease-val">0.00</span></label>
    <label>Cluster: <input type="range" id="cluster-strength" min="0" max="30" value="10"> <span class="val" id="cluster-val">0.10</span></label>
    <button class="action-btn" id="zoom-fit">Zoom to fit</button>
</div>

<div id="title-bar">
    Language Transfer Map &mdash; <span id="node-count"></span> languages, <span id="link-count"></span> links
</div>

<script>
const DATA = __DATA_PLACEHOLDER__;

let width = window.innerWidth, height = window.innerHeight;
let centerX = width / 2, centerY = height / 2;
let clusterRadius = Math.min(width, height) * 0.3;

const svg = d3.select("#graph").attr("width", width).attr("height", height);
const g = svg.append("g");

const zoom = d3.zoom().scaleExtent([0.2, 5]).on("zoom", e => g.attr("transform", e.transform));
svg.call(zoom);

const nodes = DATA.nodes;
const allLinks = DATA.links;
const familyColors = DATA.familyColors;
const familyAngles = DATA.familyAngles;
const nodeById = new Map(nodes.map(n => [n.id, n]));

let linkThreshold = 0.50;
let easeThreshold = 0.00;
let activeFamilies = new Set();
let showPortfolio = true;
let showTargets = true;
let showLiving = true;
let showHistorical = false;
let clusterStrength = 0.10;

function isNodeVisible(d) {
    if (d.historical && !showHistorical) return false;
    if (!d.historical && !showLiving) return false;
    if (d.type === "portfolio") {
        if (!showPortfolio) return false;
        if (activeFamilies.size > 0 && !activeFamilies.has(d.family)) return false;
        return true;
    }
    if (!showTargets) return false;
    if (d.ease !== null && d.ease < easeThreshold) return false;
    if (activeFamilies.size > 0 && !activeFamilies.has(d.family)) return false;
    return true;
}

function visibleLinks() {
    return allLinks.filter(l => {
        if (l.weight < linkThreshold) return false;
        const sid = typeof l.source === "object" ? l.source.id : l.source;
        const tid = typeof l.target === "object" ? l.target.id : l.target;
        const sn = nodeById.get(sid), tn = nodeById.get(tid);
        return sn && tn && isNodeVisible(sn) && isNodeVisible(tn);
    });
}

function linkId(l) {
    const s = typeof l.source === "object" ? l.source.id : l.source;
    const t = typeof l.target === "object" ? l.target.id : l.target;
    return s + "|" + t;
}

function clusterPos(family) {
    const angle = familyAngles[family] || 0;
    return { x: centerX + clusterRadius * Math.cos(angle), y: centerY + clusterRadius * Math.sin(angle) };
}

nodes.forEach(d => {
    const pos = clusterPos(d.family);
    d.x = pos.x + (Math.random() - 0.5) * 45;
    d.y = pos.y + (Math.random() - 0.5) * 45;
});

const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink([]).id(d => d.id)
        .distance(d => 200 - d.weight * 135).strength(d => d.weight * 0.08))
    .force("charge", d3.forceManyBody().strength(-60))
    .force("center", d3.forceCenter(centerX, centerY).strength(0.02))
    .force("collision", d3.forceCollide().radius(d => d.radius + 18))
    .force("clusterX", d3.forceX(d => clusterPos(d.family).x).strength(clusterStrength))
    .force("clusterY", d3.forceY(d => clusterPos(d.family).y).strength(clusterStrength))
    .stop();

const linkG = g.append("g");
function renderLinks() {
    const vl = visibleLinks();
    const sel = linkG.selectAll("line").data(vl, linkId);
    sel.exit().remove();
    sel.enter().append("line")
        .attr("class", d => d.type === "portfolio" ? "link-portfolio" : "link-transfer")
        .attr("stroke", d => {
            const sid = typeof d.source === "object" ? d.source.id : d.source;
            return familyColors[(nodeById.get(sid) || {}).family] || "#555";
        })
        .attr("stroke-width", d => 0.5 + d.weight * 4);
    return linkG.selectAll("line");
}

const nodeG = g.append("g");
const nodeEl = nodeG.selectAll("circle")
    .data(nodes).join("circle")
    .attr("class", d => d.type === "portfolio" ? "node-portfolio" : "node-target")
    .attr("r", d => d.radius)
    .attr("fill", d => familyColors[d.family] || "#888")
    .attr("fill-opacity", d => d.type === "portfolio" ? 1.0 : 0.4)
    .attr("stroke", d => familyColors[d.family] || "#888")
    .on("mouseover", handleMouseOver)
    .on("mouseout", handleMouseOut)
    .call(d3.drag()
        .on("start", (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag",  (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end",   (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));

const labelG = g.append("g");
const labelEl = labelG.selectAll("text")
    .data(nodes).join("text")
    .attr("class", d => "label" + (d.type === "portfolio" ? " label-portfolio" : ""))
    .attr("dy", d => d.radius + 14)
    .text(d => d.id);

let linkEl = renderLinks();

function applyFilters(autoZoom) {
    const visNodes = nodes.filter(isNodeVisible);
    const visLinks = visibleLinks();

    nodeEl.style("display", d => isNodeVisible(d) ? null : "none");
    labelEl.style("display", d => isNodeVisible(d) ? null : "none");
    linkEl = renderLinks();

    document.getElementById("node-count").textContent = visNodes.length;
    document.getElementById("link-count").textContent = visLinks.length;

    simulation.force("link", d3.forceLink(visLinks).id(d => d.id)
        .distance(d => 200 - d.weight * 135).strength(d => d.weight * 0.08));
    simulation.alpha(0.3).restart();

    if (autoZoom && visNodes.length > 0) zoomToVisible(visNodes);
}

function zoomToVisible(visNodes) {
    if (!visNodes.length) return;
    const pad = 80;
    const xs = visNodes.map(d => d.x || centerX);
    const ys = visNodes.map(d => d.y || centerY);
    const x0 = Math.min(...xs) - pad, x1 = Math.max(...xs) + pad;
    const y0 = Math.min(...ys) - pad, y1 = Math.max(...ys) + pad;
    const sc = Math.min(width * 0.9 / (x1 - x0), height * 0.9 / (y1 - y0), 4);
    svg.transition().duration(500).call(zoom.transform,
        d3.zoomIdentity.translate(width / 2 - sc * (x0 + x1) / 2, height / 2 - sc * (y0 + y1) / 2).scale(sc));
}

simulation.on("tick", () => {
    linkEl
        .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
    nodeEl.attr("cx", d => d.x).attr("cy", d => d.y);
    labelEl.attr("x", d => d.x).attr("y", d => d.y);
});

const families = [...new Set(nodes.map(n => n.family))].sort();
const familyBtnsDiv = document.getElementById("family-buttons");
families.forEach(f => {
    const color = familyColors[f] || "#888";
    const btn = document.createElement("span");
    btn.className = "family-btn";
    btn.dataset.family = f;
    btn.style.borderColor = color;
    btn.style.background = color + "22";
    btn.innerHTML = `<span class="family-dot" style="background:${color}"></span>${f}`;
    btn.onclick = () => {
        if (activeFamilies.has(f)) activeFamilies.delete(f);
        else activeFamilies.add(f);
        btn.classList.toggle("active", activeFamilies.has(f));
        applyFilters(activeFamilies.size > 0);
    };
    familyBtnsDiv.appendChild(btn);
});

document.getElementById("family-reset").onclick = () => {
    activeFamilies.clear();
    document.querySelectorAll(".family-btn").forEach(b => b.classList.remove("active"));
    applyFilters(false);
};

document.getElementById("show-portfolio").onchange  = function() { showPortfolio  = this.checked; applyFilters(false); };
document.getElementById("show-targets").onchange    = function() { showTargets    = this.checked; applyFilters(false); };
document.getElementById("show-living").onchange     = function() { showLiving     = this.checked; applyFilters(false); };
document.getElementById("show-historical").onchange = function() { showHistorical = this.checked; applyFilters(false); };

document.getElementById("threshold").oninput = function() {
    linkThreshold = this.value / 100;
    document.getElementById("threshold-val").textContent = linkThreshold.toFixed(2);
    applyFilters(false);
};
document.getElementById("ease-threshold").oninput = function() {
    easeThreshold = this.value / 100;
    document.getElementById("ease-val").textContent = easeThreshold.toFixed(2);
    applyFilters(false);
};
document.getElementById("cluster-strength").oninput = function() {
    clusterStrength = this.value / 100;
    document.getElementById("cluster-val").textContent = clusterStrength.toFixed(2);
    simulation.force("clusterX").strength(clusterStrength);
    simulation.force("clusterY").strength(clusterStrength);
    simulation.alpha(0.4).restart();
};

document.getElementById("zoom-fit").onclick = () => zoomToVisible(nodes.filter(isNodeVisible));

document.getElementById("toggle-families").onclick = () => document.getElementById("family-panel").classList.toggle("open");
document.getElementById("toggle-controls").onclick = () => document.getElementById("controls").classList.toggle("open");
document.getElementById("close-families").onclick = () => document.getElementById("family-panel").classList.remove("open");
document.getElementById("close-controls").onclick = () => document.getElementById("controls").classList.remove("open");

const tooltip = document.getElementById("tooltip");

function handleMouseOver(event, d) {
    const connectedIds = new Set([d.id]);
    linkEl.each(function(l) {
        const sid = typeof l.source === "object" ? l.source.id : l.source;
        const tid = typeof l.target === "object" ? l.target.id : l.target;
        if (sid === d.id) connectedIds.add(tid);
        if (tid === d.id) connectedIds.add(sid);
    });
    nodeEl.classed("node-dim", n => isNodeVisible(n) && !connectedIds.has(n.id));
    linkEl.classed("link-dim", l => {
        const sid = typeof l.source === "object" ? l.source.id : l.source;
        const tid = typeof l.target === "object" ? l.target.id : l.target;
        return sid !== d.id && tid !== d.id;
    });
    linkEl.classed("link-highlight", l => {
        const sid = typeof l.source === "object" ? l.source.id : l.source;
        const tid = typeof l.target === "object" ? l.target.id : l.target;
        return sid === d.id || tid === d.id;
    });
    labelEl.classed("label-dim", n => isNodeVisible(n) && !connectedIds.has(n.id));
    d3.select(event.target).classed("node-highlight", true);

    const fc = familyColors[d.family] || "#888";
    let html = `<h3>${d.id} <span class="family-tag" style="background:${fc}">${d.family}</span></h3>`;
    if (d.type === "portfolio") html += `<div>Level: <strong>${d.level}</strong></div>`;
    if (d.ease != null) {
        html += `<div>Ease: <strong>${d.ease}</strong>`;
        if (d.proficiency > 0) html += ` <span style="color:#8b949e;font-size:12px;">(transfer ${d.transfer_ease}, +L${(d.proficiency*5).toFixed(0)} boost)</span>`;
        html += `</div>`;
        html += dimBar("Lexical",   d.lex,    "#e74c3c");
        html += dimBar("Grammar",   d.gram,   "#3498db");
        html += dimBar("Phonology", d.phon,   "#2ecc71");
        html += dimBar("Script",    d.script, "#f39c12");
        if (d.penalty < 1) html += `<div style="color:#e74c3c;font-size:12px;">Logographic penalty: x${d.penalty}</div>`;
        if (d.top_sources && d.top_sources.length > 0) {
            const visibleSources = d.top_sources.filter(s => showHistorical || !s.historical).slice(0, 3);
            if (visibleSources.length > 0)
                html += `<div class="sources">Most similar: ${visibleSources.map(s => `${s.name} (${s.sim})`).join(", ")}</div>`;
        }
    }
    tooltip.innerHTML = html;
    tooltip.style.display = "block";
    tooltip.style.left = (event.pageX + 15) + "px";
    tooltip.style.top  = (event.pageY - 10) + "px";
}

function dimBar(label, value, color) {
    const w = Math.round((value || 0) * 120);
    return `<div class="dim"><span class="dim-label">${label}</span><span>${(value||0).toFixed(2)} <span class="dim-bar" style="width:${w}px;background:${color}"></span></span></div>`;
}

function handleMouseOut() {
    nodeEl.classed("node-dim", false);
    linkEl.classed("link-dim", false).classed("link-highlight", false);
    labelEl.classed("label-dim", false);
    nodeEl.classed("node-highlight", false);
    tooltip.style.display = "none";
}

let _resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(_resizeTimer);
    _resizeTimer = setTimeout(() => {
        width = window.innerWidth;
        height = window.innerHeight;
        centerX = width / 2;
        centerY = height / 2;
        clusterRadius = Math.min(width, height) * 0.3;
        svg.attr("width", width).attr("height", height);
        simulation
            .force("center", d3.forceCenter(centerX, centerY).strength(0.02))
            .force("clusterX", d3.forceX(d => clusterPos(d.family).x).strength(clusterStrength))
            .force("clusterY", d3.forceY(d => clusterPos(d.family).y).strength(clusterStrength));
        simulation.alpha(0.1).restart();
    }, 150);
});

function reinitLayout() {
    width = window.innerWidth;
    height = window.innerHeight;
    centerX = width / 2;
    centerY = height / 2;
    clusterRadius = Math.min(width, height) * 0.3;
    svg.attr("width", width).attr("height", height);
    nodes.forEach(d => {
        const pos = clusterPos(d.family);
        d.x = pos.x + (Math.random() - 0.5) * 45;
        d.y = pos.y + (Math.random() - 0.5) * 45;
        d.vx = 0; d.vy = 0;
    });
    simulation
        .force("center", d3.forceCenter(centerX, centerY).strength(0.02))
        .force("clusterX", d3.forceX(d => clusterPos(d.family).x).strength(clusterStrength))
        .force("clusterY", d3.forceY(d => clusterPos(d.family).y).strength(clusterStrength));
}

if (width > 0) {
    applyFilters(false);
} else {
    const ro = new ResizeObserver(entries => {
        if (entries[0].contentRect.width > 0) {
            ro.disconnect();
            reinitLayout();
            applyFilters(false);
        }
    });
    ro.observe(document.body);
}
</script>
</body>
</html>"""


def build_graph_html(
    portfolio: dict[str, float],
    bundle: dict,
    pair_sims: dict[str, float],
    *,
    out_path: Path | None = None,
) -> str:
    """Build the graph and return rendered HTML string.

    If *out_path* is given, also writes to disk (for local use).
    """
    data = build_graph_data(portfolio, bundle, pair_sims)
    html = _HTML_TEMPLATE.replace("__DATA_PLACEHOLDER__", json.dumps(data, indent=None))

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")

    return html
