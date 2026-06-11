"""Core compute module for Language Transfer Map.

Compute engine: bundle loaders and all similarity/ease functions.
"""

import json
import yaml
from collections import Counter, defaultdict
from math import prod
from pathlib import Path

# ---------------------------------------------------------------------------
# Master ISO mapping: language name -> ISO 639-3 code
# ---------------------------------------------------------------------------

LANGUAGE_ISO = {
    # Romance
    "French": "fra", "Spanish": "spa", "Portuguese": "por", "Italian": "ita",
    "Romanian": "ron", "Catalan": "cat", "Galician": "glg", "Occitan": "oci",
    "Latin": "lat", "Sardinian": "sro",
    # Germanic
    "English": "eng", "German": "deu", "Dutch": "nld", "Swedish": "swe",
    "Norwegian": "nor", "Danish": "dan", "Icelandic": "isl", "Faroese": "fao",
    "Afrikaans": "afr", "Luxembourgish": "ltz", "Yiddish": "ydd",
    # Celtic
    "Breton": "bre", "Welsh": "cym", "Irish": "gle", "Scottish Gaelic": "gla",
    # Slavic
    "Russian": "rus", "Ukrainian": "ukr", "Bulgarian": "bul", "Macedonian": "mkd",
    "Serbian": "hbs", "Croatian": "hbs", "Bosnian": "hbs", "Slovenian": "slv",
    "Polish": "pol", "Czech": "ces", "Slovak": "slk", "Belarusian": "bel",
    # Baltic
    "Lithuanian": "lit", "Latvian": "lvs",
    # Greek
    "Greek": "ell",
    # Albanian
    "Albanian": "sqi",
    # Armenian
    "Armenian": "hye",
    # Indo-Iranian
    "Hindi": "hin", "Nepali": "npi", "Marathi": "mar", "Sanskrit": "san",
    "Urdu": "urd", "Persian": "pes", "Pashto": "pst", "Bengali": "ben",
    "Assamese": "asm", "Punjabi": "pan", "Gujarati": "guj", "Sinhala": "sin",
    "Kurdish": "ckb",
    # Dravidian
    "Tamil": "tam", "Telugu": "tel", "Kannada": "kan", "Malayalam": "mal",
    # Semitic
    "Standard Arabic": "arb", "Tunisian Arabic": "aeb",
    "Egyptian Arabic": "arz", "Levantine Arabic": "apc",
    "Moroccan Arabic": "ary", "Gulf Arabic": "afb",
    "Hebrew": "heb", "Amharic": "amh", "Tigrinya": "tir", "Maltese": "mlt",
    # Turkic
    "Turkish": "tur", "Azerbaijani (N.)": "azj", "Azerbaijani (S.)": "azb", "Uzbek": "uzn", "Kazakh": "kaz",
    "Kyrgyz": "kir", "Tatar": "tat", "Uyghur": "uig", "Turkmen": "tuk",
    "Bashkir": "bak",
    # Mongolic
    "Mongolian": "khk",
    # Koreanic
    "Korean": "kor",
    "Middle Korean": "okm",
    # Japonic
    "Japanese": "jpn", "Okinawan": "ryu",
    # Sino-Tibetan
    "Chinese": "cmn", "Mandarin": "cmn", "Cantonese": "yue",
    "Wu": "wuu", "Hakka": "hak", "Min Nan": "nan",
    "Tibetan": "bod", "Burmese": "mya",
    # Austronesian
    "Indonesian": "ind", "Malay": "zsm", "Tagalog": "tgl", "Javanese": "jav",
    "Malagasy": "plt",
    # Tai-Kadai
    "Thai": "tha", "Lao": "lao",
    # Austroasiatic
    "Vietnamese": "vie", "Khmer": "khm",
    # Kartvelian
    "Georgian": "kat", "Mingrelian": "xmf", "Laz": "lzz", "Svan": "sva",
    # Uralic
    "Finnish": "fin", "Estonian": "ekk", "Hungarian": "hun",
    # Niger-Congo
    "Swahili": "swh", "Yoruba": "yor", "Igbo": "ibo", "Hausa": "hau",
    "Wolof": "wol", "Zulu": "zul", "Xhosa": "xho",
    # Creole / Pidgin
    "Haitian Creole": "hat", "Tok Pisin": "tpi",
    # Constructed
    "Esperanto": "epo",
    # Polynesian / Oceanic
    "Hawaiian": "haw", "Maori": "mri", "Samoan": "smo",
    # Niger-Congo (additional)
    "Kinyarwanda": "kin", "Shona": "sna", "Lingala": "lin",
    "Bambara": "bam", "Chichewa": "nya", "Tswana": "tsn", "Luganda": "lug",
    # Austronesian (additional)
    "Cebuano": "ceb", "Sundanese": "sun",
    # Quechuan
    "Quechua": "quy",
    # Caucasian (non-Kartvelian)
    "Chechen": "che", "Avar": "ava", "Abkhaz": "abk",
    "Adyghe": "ady", "Kabardian": "kbd",
    # Native American
    "Navajo": "nav", "Cherokee": "chr", "Nahuatl": "nci",
    "Mapuche": "arn", "Yupik": "esu", "St Lawrence Yupik": "ess",
    "Inuktitut": "ike", "Kalaallisut": "kal", "Kiche": "quc",
    "Yucatec Maya": "yua",
    # Siberian / Paleosiberian
    "Evenki": "evn", "Chukchi": "ckt", "Koryak": "kpy", "Ainu": "ain",
    "Yakut": "sah", "Ket": "ket", "Nivkh": "niv",
    # Tungusic
    "Manchu": "mnc", "Even": "eve", "Nanai": "gld",
    # Turkic (extended)
    "Chuvash": "chv", "Gagauz": "gag", "Tuvan": "tyv", "Khakas": "kjh",
    # Mongolic (extended)
    "Buryat": "bua",
    # Uralic (extended)
    "North Saami": "sme", "Erzya": "myv", "Komi": "kpv",
    "Udmurt": "udm", "Mari": "mhr",
    # Dravidian (extended)
    "Brahui": "brh",
    # Austronesian (Oceanic)
    "Tongan": "ton", "Fijian": "fij",
    # Others
    "Basque": "eus", "Somali": "som",
    # IE living (new)
    "Bhojpuri": "bho", "Kashmiri": "kas", "Maithili": "mai",
    "Ossetic": "oss", "Western Armenian": "hyw",
    # IE historical — strong tier
    "Cornish": "cor", "Gothic": "got", "Ancient Greek": "grc",
    "Old Norse": "non", "Classical Armenian": "xcl",
    "Old Irish": "sga", "Old High German": "goh", "Old English": "ang",
    "Anglo-Norman": "xno", "Pali": "pli", "Middle Persian": "xmn",
    # IE historical — middle tier
    "Middle High German": "gmh", "Middle Dutch": "dum",
    "Middle Welsh": "wlm", "Middle Breton": "xbm",
    "Old Spanish": "osp", "Old Novgorod": "orv",
    # IE historical — specialist tier
    "Old Prussian": "prg", "Sogdian": "sog", "Old Persian": "peo",
    "Hittite": "hit", "Tocharian A": "xto", "Tocharian B": "txb",
    "Mycenaean Greek": "gmy", "Gaulish": "xtg", "Oscan": "osc", "Umbrian": "xum",
    # Slavic living (new)
    "Rusyn": "rue",
    # Austronesian (new — from ABVD)
    "Hiligaynon": "hil", "Minangkabau": "min", "Acehnese": "ace",
    "Kapampangan": "pam", "Iban": "iba", "Toba Batak": "bbc",
    "Tahitian": "tah", "Tausug": "tsg", "Paiwan": "pwn",
    # Bantu (new — from GrollemundBantu)
    "Kikuyu": "kik", "Kikongo": "kng", "Rukiga": "cgg",
    "Ndebele": "nde", "Runyankore": "nyn",
    # Sino-Tibetan living (new — from SagartST)
    "Garo": "grt", "Mizo": "lus", "Lisu": "lis", "Chin Hakha": "cnh",
    # Sino-Tibetan historical
    "Old Chinese": "och", "Old Tibetan": "xct", "Old Burmese": "obr",
    "Old Japanese": "ojp",
    # Austroasiatic (new)
    "Mon": "mnw", "Mundari": "unr", "Khasi": "kha",
    # Tupian (new)
    "Guaraní": "gug",
    # Semitic (new)
    "Tigre": "tig", "Ge'ez": "gez",
    "Iraqi Arabic": "acm", "Yemeni Arabic": "ayh", "Chadian Arabic": "shu",
    # Quechuan (new)
    "Imbabura Quechua": "qvi",
    # Dravidian (new)
    "Tulu": "tcy",
    # Turkic historical
    "Old Turkic": "oui",
    # Mayan (new)
    "Kaqchikel": "cak", "Mam": "mam", "Tzotzil": "tzo",
    "Q'eqchi'": "kek", "Tzeltal": "tzh", "Huastec": "hus",
    # Ancient Near Eastern / Mediterranean (ASJP only)
    "Akkadian": "akk", "Phoenician": "phn", "Ugaritic": "uga",
    "Classical Syriac": "syc", "Coptic": "cop",
    "Sumerian": "sux", "Elamite": "elx", "Etruscan": "ett",
    # Berber
    "Tamazight": "tzm", "Kabyle": "kab", "Tachelhit": "shi",
    # Nilo-Saharan
    "Kanuri": "knc", "Luo": "luo",
    # Khoisan
    "Khoekhoe": "naq",
    # Hmong-Mien
    "Hmong": "hnj",
    # Gbe (Niger-Congo)
    "Ewe": "ewe", "Fon": "fon",
    # Algonquian
    "Cree": "crk",
    # Siouan
    "Lakota": "lkt",
    # Cushitic (additional)
    "Beja": "bej",
    # Isolates
    "Burushaski": "bsk", "Tlingit": "tli",
    # NE Caucasian (additional)
    "Lezgi": "lez", "Ingush": "inh", "Lak": "lbe", "Dargi": "dar",
    # Uralic — Samoyedic
    "Nenets": "yrk", "Nganasan": "nio", "Selkup": "sel",
    "Kamas": "xas",
    # Yukaghir
    "Yukaghir": "yux", "Kolyma Yukaghir": "ykg",
    # Mongolic (extended)
    "Kalmyk": "xal",
    # Ugric (extended)
    "Khanty": "kca", "Mansi": "mns",
    # Iranian (extended)
    "Kurmanji": "kmr",
    # Northwest Caucasian — historical
    "Ubykh": "uby",
    # Saami (extended)
    "Southern Saami": "sma", "Kildin Saami": "sjd",
    # Aymaran
    "Aymara": "ayr",
}

# ISO 639-3 -> wordfreq/loanword code
ISO3_TO_WF: dict = {
    "fra": "fr", "spa": "es", "por": "pt", "ita": "it", "ron": "ro",
    "cat": "ca",
    "oci": "oc", "lat": "la", "sro": "sc", "glg": "gl",
    "eng": "en", "deu": "de", "nld": "nl", "swe": "sv", "nor": "nb",
    "dan": "da", "isl": "is",
    "afr": "af", "ydd": "yi", "fao": "fo", "ltz": "lb",
    "bre": "br", "cym": "cy", "gle": "ga", "gla": "gd",
    "rus": "ru", "ukr": "uk", "pol": "pl", "ces": "cs", "slk": "sk",
    "bul": "bg", "mkd": "mk", "hbs": "sh",
    "slv": "sl", "bel": "be", "lit": "lt", "lvs": "lv",
    "ell": "el", "grc": "grc",
    "sqi": "sq", "hye": "hy",
    "arb": "ar", "aeb": "ar", "arz": "ar", "apc": "ar", "heb": "he",
    "ary": "ary", "afb": "afb", "mlt": "mt", "amh": "am", "tir": "ti",
    "pes": "fa",
    "pst": "ps",
    "hin": "hi", "urd": "ur", "ben": "bn", "tam": "ta",
    "san": "sa", "npi": "ne", "mar": "mr", "pan": "pa",
    "guj": "gu", "sin": "si", "asm": "as",
    "tel": "te", "kan": "kn", "mal": "ml",
    "tur": "tr",
    "azj": "az", "azb": "az", "kaz": "kk", "uzn": "uz", "kir": "ky",
    "tat": "tt", "uig": "ug", "tuk": "tk", "bak": "ba",
    "khk": "mn",
    "ckb": "ckb",
    "cmn": "zh", "jpn": "ja", "kor": "ko",
    "yue": "zh", "wuu": "zh", "hak": "zh", "nan": "zh",
    "ryu": "ja",
    "bod": "bo", "mya": "my",
    "vie": "vi", "ind": "id", "zsm": "ms", "tgl": "fil",
    "tha": "th", "lao": "lo", "khm": "km", "jav": "jv",
    "kat": "ka",
    "fin": "fi", "hun": "hu", "ekk": "et",
    "plt": "mg", "mri": "mi", "smo": "sm", "haw": "haw",
    "ceb": "ceb", "sun": "su",
    "swh": "sw", "yor": "yo", "ibo": "ig", "hau": "ha",
    "wol": "wo", "zul": "zu", "xho": "xh",
    "kin": "rw", "sna": "sn", "lin": "ln", "bam": "bm",
    "nya": "ny", "tsn": "tn", "lug": "lg",
    "hat": "ht", "tpi": "tpi", "epo": "eo",
    "som": "so",
    "che": "ce", "ava": "av", "abk": "ab",
    "eus": "eu",
    "nci": "nci",
    "mnc": "mnc", "eve": "eve", "gld": "gld",
    "chv": "cv", "gag": "gag", "tyv": "tyv", "kjh": "kjh",
    "bua": "bua",
    "sme": "se", "myv": "myv", "kpv": "kpv", "udm": "udm", "mhr": "mhr",
    "brh": "brh",
    "ton": "to", "fij": "fj",
    "bho": "bho", "kas": "ks", "mai": "mai", "oss": "os",
    "hyw": "hy",
    "cor": "kw",
    "got": "got", "grc": "grc", "non": "non", "xcl": "xcl",
    "sga": "sga", "goh": "goh", "xno": "xno", "pli": "pli", "xmn": "xmn",
    "gmh": "gmh", "dum": "dum", "wlm": "wlm", "xbm": "xbm",
    "osp": "osp", "orv": "orv",
    "prg": "prg", "sog": "sog", "peo": "peo", "hit": "hit",
    "xto": "xto", "txb": "txb", "gmy": "gmy", "xtg": "xtg", "osc": "osc", "xum": "xum",
    "rue": "rue",
    "hil": "hil", "min": "min", "ace": "ace", "pam": "pam",
    "iba": "iba", "bbc": "bbc", "tah": "ty", "tsg": "tsg", "pwn": "pwn",
    "kik": "ki", "kng": "kg", "cgg": "cgg", "nde": "nd", "nyn": "nyn",
    "grt": "grt", "lus": "lus", "lis": "lis", "cnh": "cnh",
    "ojp": "ojp", "och": "och", "xct": "xct", "obr": "obr",
    "mnw": "mnw", "unr": "unr", "kha": "kha",
    "gug": "gn",
    "tig": "tig", "gez": "gez",
    "acm": "ar", "ayh": "ar", "shu": "ar",
    "qvi": "qvi",
    "tcy": "tcy",
    "oui": "oui",
    "cak": "cak", "mam": "mam", "tzo": "tzo",
    "kek": "kek", "tzh": "tzh", "hus": "hus",
    "akk": "akk", "phn": "phn", "uga": "uga",
    "syc": "syc", "cop": "cop",
    "sux": "sux", "elx": "elx", "ett": "ett",
}

# Cross-family lexical authorizations
_LEX_FAMILY_AUTH: dict[str, set] = {
    "hat": {"Romance"},
    "tpi": {"Germanic"},
    "epo": {"Romance", "Germanic", "Slavic"},
    "mlt": {"Romance"},
    "cop": {"Semitic"},
    "hau": {"Semitic"},
    "som": {"Semitic"},
    "bod": {"Chinese", "Burmese-Lolo"},
    "tzm": {"Semitic"},
    "kab": {"Semitic"},
    "shi": {"Semitic"},
    "bej": {"Semitic", "Lowland East Cushitic"},
    "tli": {"Athapaskan"},
}

# Manual genus overrides for languages absent from WALS genus data
_GENUS_OVERRIDE: dict = {
    "lat": "Italic", "sro": "Romance", "hbs": "Slavic", "ydd": "Germanic",
    "azj": "Turkic", "azb": "Turkic", "uzn": "Turkic",
    "lvs": "Baltic", "npi": "Indic", "san": "Indic",
    "zsm": "Malayo-Sumbawan",
    "got": "Germanic", "non": "Germanic", "goh": "Germanic",
    "ang": "Germanic", "gmh": "Germanic", "dum": "Germanic",
    "sga": "Celtic", "wlm": "Celtic", "xbm": "Celtic", "xtg": "Celtic",
    "xno": "Romance", "osp": "Romance", "fro": "Romance", "pro": "Romance",
    "osc": "Italic", "xum": "Italic",
    "orv": "Slavic", "rue": "Slavic",
    "prg": "Baltic",
    "grc": "Greek", "gmy": "Greek",
    "xcl": "Armenian",
    "pli": "Indic", "xmn": "Iranian", "sog": "Iranian", "peo": "Iranian",
    "hit": "Hittite-Luwian",
    "xto": "Tocharic", "txb": "Tocharic",
    "oui": "Turkic",
    "okm": "Korean",
    "ojp": "Japanese",
    "och": "Chinese", "xct": "Bodic", "obr": "Burmese-Lolo",
    "bua": "Mongolic",
    "gez": "Semitic",
    "akk": "Semitic", "phn": "Semitic", "uga": "Semitic", "syc": "Semitic",
    "ayh": "Semitic",
    "che": "Northeast-Caucasian", "ava": "Northeast-Caucasian",
    "lez": "Northeast-Caucasian", "inh": "Northeast-Caucasian",
    "lbe": "Northeast-Caucasian", "dar": "Northeast-Caucasian",
}


# ---------------------------------------------------------------------------
# Bundle loaders — read from pre-computed slim JSON files
# ---------------------------------------------------------------------------

def _load_asjp_by_iso(bundle_dir: Path) -> dict[str, dict[str, list[str]]]:
    with open(bundle_dir / "asjp_slim.json", encoding="utf-8") as f:
        return json.load(f)


def _load_wals_by_iso(bundle_dir: Path) -> dict[str, dict[str, str]]:
    with open(bundle_dir / "wals_slim.json", encoding="utf-8") as f:
        data = json.load(f)
    return data["features"]


def _load_phoible_by_iso(bundle_dir: Path) -> dict[str, set[str]]:
    with open(bundle_dir / "phoible_slim.json", encoding="utf-8") as f:
        data = json.load(f)
    return {iso: set(phonemes) for iso, phonemes in data.items()}


def _load_wals_genus(bundle_dir: Path) -> dict[str, str]:
    with open(bundle_dir / "wals_slim.json", encoding="utf-8") as f:
        data = json.load(f)
    iso_to_genus = data["genus"]
    iso_to_genus.update(_GENUS_OVERRIDE)
    return iso_to_genus


def _load_loanword_scores(bundle_dir: Path) -> dict:
    with open(bundle_dir / "loanword_scores_extended.json", encoding="utf-8") as f:
        return json.load(f)


def _load_scripts(bundle_dir: Path) -> dict:
    with open(bundle_dir / "scripts.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_cognate_sims(bundle_dir: Path) -> dict[tuple[str, str], float]:
    with open(bundle_dir / "cognate_sims.json", encoding="utf-8") as f:
        raw = json.load(f)
    result = {}
    for key, val in raw.items():
        iso1, iso2 = key.split("|")
        result[(iso1, iso2)] = val
        result[(iso2, iso1)] = val
    return result


def _load_asjp_calibration(bundle_dir: Path) -> tuple[float, float, float]:
    with open(bundle_dir / "asjp_calibration.json", encoding="utf-8") as f:
        data = json.load(f)
    return (data["slope"], data["beta_genus"], data["intercept"])


def load_bundle(bundle_dir: Path) -> dict:
    """Load all pre-computed data from the bundle directory.

    Returns a dict with keys: asjp, wals, phoible, scripts, loanword,
    iso_to_genus, genus_data, phoible_genus_data, cognate_sims, asjp_calibration.
    """
    asjp = _load_asjp_by_iso(bundle_dir)
    wals = _load_wals_by_iso(bundle_dir)
    phoible = _load_phoible_by_iso(bundle_dir)
    scripts = _load_scripts(bundle_dir)
    loanword = _load_loanword_scores(bundle_dir)
    iso_to_genus = _load_wals_genus(bundle_dir)
    cognate_sims = _load_cognate_sims(bundle_dir)
    asjp_calibration = _load_asjp_calibration(bundle_dir)

    genus_protos = _build_genus_protos(wals, iso_to_genus)
    genus_data = (iso_to_genus, genus_protos)
    phoible_protos = _build_phoible_genus_protos(phoible, iso_to_genus)
    phoible_genus_data = (iso_to_genus, phoible_protos)

    return {
        "asjp": asjp,
        "wals": wals,
        "phoible": phoible,
        "scripts": scripts,
        "loanword": loanword,
        "iso_to_genus": iso_to_genus,
        "genus_data": genus_data,
        "phoible_genus_data": phoible_genus_data,
        "cognate_sims": cognate_sims,
        "asjp_calibration": asjp_calibration,
    }


# ---------------------------------------------------------------------------
# Prototype builders
# ---------------------------------------------------------------------------

def _build_genus_protos(wals: dict, iso_to_genus: dict, min_feats: int = 30) -> dict:
    genus_feat_counters: dict = defaultdict(lambda: defaultdict(Counter))
    for iso, vals in wals.items():
        if len(vals) < min_feats:
            continue
        genus = iso_to_genus.get(iso)
        if not genus:
            continue
        for feat, val in vals.items():
            genus_feat_counters[genus][feat][val] += 1

    protos: dict = {}
    for genus, feat_counters in genus_feat_counters.items():
        protos[genus] = {
            feat: counter.most_common(1)[0][0]
            for feat, counter in feat_counters.items()
        }
    return protos


def _build_phoible_genus_protos(phoible: dict, iso_to_genus: dict) -> dict[str, set[str]]:
    genus_members: dict[str, list[str]] = {}
    for iso in phoible:
        genus = iso_to_genus.get(iso)
        if genus:
            genus_members.setdefault(genus, []).append(iso)

    protos: dict[str, set[str]] = {}
    for genus, members in genus_members.items():
        n = len(members)
        counts: dict[str, int] = {}
        for iso in members:
            for phoneme in phoible[iso]:
                counts[phoneme] = counts.get(phoneme, 0) + 1
        protos[genus] = {p for p, c in counts.items() if c > n / 2}
    return protos


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _norm_edit_dist(s1: str, s2: str) -> float:
    if s1 == s2:
        return 0.0
    if not s1 or not s2:
        return 1.0
    m, n = len(s1), len(s2)
    prev = list(range(n + 1))
    for i, c1 in enumerate(s1, 1):
        curr = [i] + [0] * n
        for j, c2 in enumerate(s2, 1):
            if c1 == c2:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return prev[n] / max(m, n)


def _lex_sim(forms1: dict, forms2: dict) -> float:
    shared = set(forms1.keys()) & set(forms2.keys())
    if not shared:
        return 0.0
    total = 0.0
    for c in shared:
        total += 1.0 - min(
            _norm_edit_dist(f1, f2)
            for f1 in forms1[c]
            for f2 in forms2[c]
        )
    return total / len(shared)


def _gram_sim(vals1: dict, vals2: dict) -> float:
    shared = set(vals1.keys()) & set(vals2.keys())
    if not shared:
        return 0.0
    return sum(1 for f in shared if vals1[f] == vals2[f]) / len(shared)


def _lex_genus_ok(iso1: str, g1, iso2: str, g2) -> bool:
    if g1 and g2 and g1 == g2:
        return True
    if g2 and g2 in _LEX_FAMILY_AUTH.get(iso1, ()):
        return True
    if g1 and g1 in _LEX_FAMILY_AUTH.get(iso2, ()):
        return True
    return False


# ---------------------------------------------------------------------------
# Compute functions
# ---------------------------------------------------------------------------

def compute_lexical(
    portfolio: dict,
    target_iso: str,
    asjp: dict,
    loanword: dict,
    cognate_sims: dict = None,
    iso_to_genus: dict = None,
    asjp_calibration: "tuple | None" = None,
) -> tuple:
    wf_target = ISO3_TO_WF.get(target_iso)
    lw_target = loanword.get(wf_target, {}) if wf_target else {}

    if not lw_target and not cognate_sims:
        return 0.0, []

    contributions = []
    for name, level in portfolio.items():
        if level <= 0:
            continue
        iso = LANGUAGE_ISO.get(name)
        if not iso or iso == target_iso:
            continue

        lex_sim = 0.0
        if cognate_sims:
            lex_sim = cognate_sims.get((iso, target_iso)) or cognate_sims.get((target_iso, iso)) or 0.0

        if lex_sim == 0.0 and asjp_calibration and iso in asjp and target_iso in asjp:
            g_src = iso_to_genus.get(iso) if iso_to_genus else None
            g_tgt = iso_to_genus.get(target_iso) if iso_to_genus else None
            if _lex_genus_ok(iso, g_src, target_iso, g_tgt):
                slope, beta_genus, intercept = asjp_calibration
                raw = _lex_sim(asjp[iso], asjp[target_iso])
                lex_sim = max(0.0, min(1.0, slope * raw + beta_genus + intercept))

        wf_src = ISO3_TO_WF.get(iso)
        lw_score = lw_target.get(wf_src, 0.0) if wf_src else 0.0

        combined = 1.0 - (1.0 - lex_sim) * (1.0 - lw_score)
        weight = level / 5.0
        c = combined * weight
        if c > 0:
            contributions.append((name, combined, c))

    if iso_to_genus and contributions:
        by_genus: dict[str, tuple] = {}
        for entry in contributions:
            src_iso = LANGUAGE_ISO.get(entry[0])
            genus = iso_to_genus.get(src_iso, src_iso or entry[0])
            if genus not in by_genus or entry[2] > by_genus[genus][2]:
                by_genus[genus] = entry
        contributions = sorted(by_genus.values(), key=lambda x: -x[2])
    else:
        contributions.sort(key=lambda x: -x[2])

    if not contributions:
        return 0.0, contributions

    score = 1.0 - prod(1.0 - c for _, _, c in contributions)
    return min(score, 1.0), contributions


def compute_grammar(
    portfolio: dict,
    target_iso: str,
    wals: dict,
    genus_data: tuple = None,
) -> tuple:
    target_vals = wals.get(target_iso)
    iso_to_genus, genus_protos = genus_data if genus_data else (None, None)

    target_from_proto = False
    if iso_to_genus and genus_protos and not target_vals:
        genus = iso_to_genus.get(target_iso)
        if genus and genus in genus_protos:
            target_vals = genus_protos[genus]
            target_from_proto = True

    if not target_vals:
        return 0.0, []

    contributions = []
    for name, level in portfolio.items():
        if level <= 0:
            continue
        iso = LANGUAGE_ISO.get(name)
        if not iso or iso == target_iso:
            continue

        raw_vals = wals.get(iso, {})
        shared_feats = len(set(raw_vals) & set(target_vals))
        alpha = min(1.0, shared_feats / 20.0)

        raw_sim = _gram_sim(raw_vals, target_vals) if raw_vals else 0.0

        family_sim = 0.0
        if alpha < 1.0 and iso_to_genus and genus_protos:
            genus = iso_to_genus.get(iso)
            proto = genus_protos.get(genus, {}) if genus else {}
            if proto:
                family_sim = _gram_sim(proto, target_vals)

        if alpha < 1.0 and family_sim == 0.0:
            alpha = max(alpha, 0.3)

        sim = alpha * raw_sim + (1.0 - alpha) * family_sim
        c = sim * (level / 5.0)
        if c > 0:
            contributions.append((name, sim, c))

    contributions.sort(key=lambda x: -x[2])
    if not contributions:
        return 0.0, contributions

    score = contributions[0][2]
    return min(score, 1.0), contributions


def compute_phonology(
    portfolio: dict[str, float],
    target_iso: str,
    phoible: dict[str, set],
    genus_data: tuple = None,
) -> tuple[float, int]:
    target_inv = phoible.get(target_iso)
    if not target_inv and genus_data:
        iso_to_genus, phoible_protos = genus_data
        genus = iso_to_genus.get(target_iso)
        if genus and genus in phoible_protos:
            target_inv = phoible_protos[genus]
    if not target_inv:
        return 0.5, 0

    known_union = set()
    for name, level in portfolio.items():
        if level < 2:
            continue
        iso = LANGUAGE_ISO.get(name)
        if not iso or iso not in phoible:
            continue
        known_union |= phoible[iso]

    if not target_inv:
        return 1.0, 0
    cov = len(known_union & target_inv) / len(target_inv)
    new_count = len(target_inv - known_union)
    return cov, new_count


def compute_script(
    portfolio: dict[str, float],
    target_name: str,
    scripts_data: dict,
) -> tuple[float, float, str]:
    lang_scripts_map = scripts_data.get("language_scripts", {})
    scripts_info = scripts_data.get("scripts", {})
    transfer_matrix = scripts_data.get("transfer", {})

    target_scripts = lang_scripts_map.get(target_name, ["latin"])

    target_iso = LANGUAGE_ISO.get(target_name)
    known_scripts = set()
    known_scripts_levels: dict[str, float] = {}
    for name, level in portfolio.items():
        if level <= 0 or LANGUAGE_ISO.get(name) == target_iso:
            continue
        for s in lang_scripts_map.get(name, []):
            known_scripts.add(s)
            known_scripts_levels[s] = max(known_scripts_levels.get(s, 0), level)

    access_scores = []
    for ts in target_scripts:
        if ts in known_scripts:
            access_scores.append(1.0)
            continue

        info = scripts_info.get(ts, {})
        diff = info.get("difficulty", 3)
        diff_norm = (diff - 1) / 4.0

        best_transfer = 0.0
        for ks in known_scripts:
            t = transfer_matrix.get(ks, {}).get(ts, 0.0)
            best_transfer = max(best_transfer, t)

        access = 1.0 - diff_norm * (1.0 - best_transfer)
        access_scores.append(access)

    script_access = max(access_scores) if access_scores else 0.5

    logographic_scripts = {s for s, info in scripts_info.items()
                          if info.get("type") == "logographic"}
    target_logographic = [s for s in target_scripts if s in logographic_scripts]

    if target_logographic:
        # BUG FIX (2026-06-11): build full script-level map from the entire portfolio,
        # including the target language itself. The `known_scripts` set above intentionally
        # excludes the target by ISO (correct for script *access*), but that exclusion
        # breaks the penalty when the target is already in the portfolio:
        #   - Chinese L5 → Mandarin: Mandarin excluded → no logographic known → 0.7 penalty (wrong)
        #   - Chinese L5 → Wu: different ISO so Chinese IS included, but transfer matrix has no
        #     self-entry for chinese_simplified→chinese_simplified → 0.7 penalty (wrong)
        # Fix: build full_logo_levels without ISO exclusion; add a direct-match path that
        # short-circuits without the transfer matrix when the learner already knows the script.
        full_logo_levels: dict[str, float] = {}
        for name, level in portfolio.items():
            if level <= 0:
                continue
            for s in lang_scripts_map.get(name, []):
                full_logo_levels[s] = max(full_logo_levels.get(s, 0), level)

        best_logo_transfer = 0.0
        for ts in target_logographic:
            # Direct: already know this exact logographic script (no transfer loss)
            if ts in full_logo_levels:
                best_logo_transfer = max(best_logo_transfer, full_logo_levels[ts] / 5.0)
            # Transfer: know a related logographic script (e.g. Chinese → Kanji)
            for ks, ks_level in full_logo_levels.items():
                if ks in logographic_scripts or ks in ("hiragana", "katakana"):
                    t = transfer_matrix.get(ks, {}).get(ts, 0.0)
                    best_logo_transfer = max(best_logo_transfer, t * ks_level / 5.0)
        script_penalty = 1.0 - 0.3 * (1.0 - best_logo_transfer)
        notes = f"logographic penalty: x{script_penalty:.2f}"
    else:
        script_penalty = 1.0
        notes = ""

    return script_access, script_penalty, notes


def compute_ease(
    target_name: str,
    target_iso: str,
    portfolio: dict,
    asjp: dict, wals: dict, phoible: dict, scripts_data: dict,
    loanword: dict, genus_data: tuple = None, phoible_genus_data: tuple = None,
    cognate_sims: dict = None, asjp_calibration: "tuple | None" = None,
) -> dict:
    iso_to_genus = genus_data[0] if genus_data else None
    lex_score, lex_detail = compute_lexical(portfolio, target_iso, asjp, loanword, cognate_sims, iso_to_genus, asjp_calibration)
    gram_score, gram_detail = compute_grammar(portfolio, target_iso, wals, genus_data)
    phon_score, phon_new = compute_phonology(portfolio, target_iso, phoible, phoible_genus_data)
    script_access, script_penalty, script_notes = compute_script(
        portfolio, target_name, scripts_data)

    ease_raw = (0.45 * lex_score
                + 0.30 * gram_score
                + 0.15 * phon_score
                + 0.10 * script_access)
    transfer_ease = ease_raw * script_penalty

    target_level = portfolio.get(target_name, 0.0)
    prof = target_level / 5.0
    lex_ease    = lex_score    + (1.0 - lex_score)    * prof
    gram_ease   = gram_score   + (1.0 - gram_score)   * prof
    phon_ease   = phon_score   + (1.0 - phon_score)   * prof
    script_ease = script_access + (1.0 - script_access) * prof
    ease = (0.45 * lex_ease + 0.30 * gram_ease
            + 0.15 * phon_ease + 0.10 * script_ease) * script_penalty

    return {
        "name":           target_name,
        "iso":            target_iso,
        "ease":           ease,
        "ease_raw":       ease_raw,
        "transfer_ease":  transfer_ease,
        "proficiency":    prof,
        "lexical":        lex_ease,
        "grammar":        gram_ease,
        "phonology":      phon_ease,
        "script_access":  script_ease,
        "script_penalty": script_penalty,
        "script_notes":   script_notes,
        "lex_detail":     lex_detail,
        "gram_detail":    gram_detail,
        "phon_new_count": phon_new,
    }


def _bottleneck(r: dict) -> str:
    if r["ease"] >= 0.85:
        return "—"
    dims = [
        ("Lexical", r["lexical"]),
        ("Grammar", r["grammar"]),
        ("Phonology", r["phonology"]),
        ("Script", r["script_access"]),
    ]
    if r["script_penalty"] < 1.0:
        dims.append(("Script (logographic)", r["script_access"] * r["script_penalty"]))
    dims.sort(key=lambda x: x[1])
    worst_name, worst_val = dims[0]
    if worst_val >= 0.9:
        return "—"
    note = f"{worst_name} ({worst_val:.2f})"
    if worst_name == "Grammar" and worst_val < 0.1:
        note += ", limited WALS data"
    return note


def _best_sources(r: dict) -> str:
    sources: dict = {}
    if r["lex_detail"]:
        sources.setdefault(r["lex_detail"][0][0], []).append("lex")
    if r["gram_detail"]:
        sources.setdefault(r["gram_detail"][0][0], []).append("gram")
    if not sources:
        return "—"
    return ", ".join(f"{n} ({', '.join(dims)})" for n, dims in sources.items())


def compute_script_access(portfolio: dict, scripts_data: dict) -> list:
    lang_scripts_map = scripts_data.get("language_scripts", {})
    scripts_info = scripts_data.get("scripts", {})
    script_sources: dict = {}
    for name, level in portfolio.items():
        if level <= 0:
            continue
        for s in lang_scripts_map.get(name, []):
            script_sources.setdefault(s, []).append((name, level))
    all_scripts_used: dict = {}
    for name in LANGUAGE_ISO:
        for s in lang_scripts_map.get(name, []):
            all_scripts_used.setdefault(s, []).append(name)
    rows = []
    for script_id, info in scripts_info.items():
        sources = script_sources.get(script_id, [])
        users = all_scripts_used.get(script_id, [])
        if not users:
            continue
        non_portfolio = [u for u in users if u not in portfolio]
        source_str = ", ".join(
            f"{n} (L{l:.0f})" for n, l in sorted(sources, key=lambda x: -x[1])[:4]
        )
        rows.append({
            "script": info.get("name", script_id),
            "type": info.get("type", ""),
            "difficulty": info.get("difficulty", 0),
            "known": bool(sources),
            "sources": source_str if sources else "—",
            "gated": non_portfolio,
        })
    return rows


def pairwise_similarity(
    iso1: str, iso2: str,
    asjp: dict, wals: dict, phoible: dict,
    phoible_genus_data: tuple = None,
    cognate_sims: dict = None,
    asjp_calibration: tuple = None,
    genus_data: tuple = None,
) -> float:
    dims = []
    key = (iso1, iso2)
    if cognate_sims and key in cognate_sims:
        dims.append((0.50, cognate_sims[key]))
    elif iso1 in asjp and iso2 in asjp:
        raw = _lex_sim(asjp[iso1], asjp[iso2])
        if asjp_calibration:
            slope, beta_genus, intercept = asjp_calibration
            g1 = genus_data[0].get(iso1) if genus_data else None
            g2 = genus_data[0].get(iso2) if genus_data else None
            if _lex_genus_ok(iso1, g1, iso2, g2):
                cal = max(0.0, min(1.0, slope * raw + beta_genus + intercept))
            elif g1 and g2:
                return 0.0
            elif iso1 in _LEX_FAMILY_AUTH or iso2 in _LEX_FAMILY_AUTH:
                return 0.0
            else:
                cal = max(0.0, min(1.0, slope * raw + intercept))
        else:
            cal = raw
        dims.append((0.50, cal))
    else:
        return 0.0

    def _wals_eff(iso):
        raw = wals.get(iso, {})
        if len(raw) < 10 and genus_data:
            iso_to_g, g_protos = genus_data
            g = iso_to_g.get(iso)
            if g and g in g_protos:
                return g_protos[g]
        return raw

    v1, v2 = _wals_eff(iso1), _wals_eff(iso2)
    if v1 and v2:
        n_shared = len(set(v1) & set(v2))
        confidence = min(1.0, n_shared / 20.0)
        dims.append((0.30, _gram_sim(v1, v2) * confidence))

    def _phoible_inv(iso):
        inv = phoible.get(iso)
        if inv is None and phoible_genus_data:
            iso_to_genus, phoible_protos = phoible_genus_data
            genus = iso_to_genus.get(iso)
            if genus:
                inv = phoible_protos.get(genus)
        return inv

    inv1, inv2 = _phoible_inv(iso1), _phoible_inv(iso2)
    if inv1 and inv2:
        shared = len(inv1 & inv2)
        union = len(inv1 | inv2)
        dims.append((0.20, shared / union if union else 0.0))

    if not dims:
        return 0.0
    total_w = sum(w for w, _ in dims)
    return sum(w * v for w, v in dims) / total_w
