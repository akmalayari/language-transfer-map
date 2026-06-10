# Methodology

## Scoring overview

Each target language receives an **ease score** from 0 to 1, computed as a weighted sum of four dimensions:

| Dimension | Weight |
|-----------|--------|
| Lexical   | 45%    |
| Grammar   | 30%    |
| Phonology | 15%    |
| Script    | 10%    |

**Proficiency modifier** is applied per dimension before weighting:

```
dim_ease = dim_score + (1 − dim_score) × level / 5
```

A level-5 language contributes fully; a level-0 language contributes nothing (it appears as a target in the graph but not as a transfer source). The aggregate form `ease = transfer + (1 − transfer) × level/5` holds by linearity of the weighted sum and is a useful shorthand, but the per-dimension form is the actual computation.

---

## Lexical similarity

**Formula:** max-per-genus independence — `1 − ∏(1 − c_g)` where each `c_g = combined_sim × level/5` is the strongest contributor within genus `g` (Romance, Germanic, Slavic, …).

Within a genus, only the highest-contribution language enters the product — correlated languages (French/Spanish/Italian) share the same inherited-vocabulary signal and stacking them independently would inflate the score. Across genera, contributions compound independently.

**Combined similarity:** `combined = 1 − (1 − genetic) × (1 − loanword)`

### Genetic similarity — cognate datasets

Curated cognate proportions: fraction of shared inherited vocabulary between language pairs. First dataset to cover a pair wins (ordered by linguistic specificity).

| Dataset | Family coverage | Key languages |
|---------|----------------|---------------|
| [IECoR v1.0](https://github.com/lexibank/iecor) | Indo-European | All IE branches |
| [Robbeets Triangulation v0.3](https://github.com/lexibank/robbeetstriangulation) | Transeurasian: Turkic, Mongolic, Tungusic, Japonic, Koreanic | Japanese, Korean, Uzbek, Mongolian, Evenki… |
| [Savelyev Turkic](https://github.com/lexibank/savelyevturkic) | Turkic (supplementary) | Tatar, Kazakh, Kyrgyz, Tuvan… |
| [Oskolskaya Tungusic](https://github.com/lexibank/oskolskayatungusic) | Tungusic | Even, Nanai, Evenki… |
| [UraLex](https://github.com/lexibank/uralex) | Uralic | Finnish, Estonian, Hungarian, Komi, Nenets… |
| [DravLex](https://github.com/lexibank/dravlex) | Dravidian | Tamil, Telugu, Kannada, Malayalam… |
| [ABVD](https://github.com/lexibank/abvd) | Austronesian | Malay/Indonesian, Tagalog, Javanese, Malagasy… |
| [Ratcliffe Arabic](https://github.com/lexibank/ratcliffearabic) | Arabic dialects | Egyptian, Levantine, Moroccan, Iraqi… |
| [Feleke Ethiosemitic](https://github.com/lexibank/felekesemitic) | Ethiopian Semitic | Amharic, Tigrinya, Ge'ez… |
| [Gravina Chadic](https://github.com/lexibank/gravinachadic) | Chadic (Afro-Asiatic) | Hausa |
| [Peiros Austroasiatic](https://github.com/lexibank/peirosaustroasiatic) | Austroasiatic | Khmer, Vietnamese, Mon… |
| [Liu Sinitic](https://github.com/lexibank/liusinitic) | Sinitic | Mandarin, Cantonese, Wu, Hakka, Min Nan |
| [Sagart Sino-Tibetan](https://github.com/lexibank/sagartst) | Sino-Tibetan | Chinese, Tibetan, Burmese, Old Chinese… |
| [Grollemund Bantu](https://github.com/lexibank/grollemundbantu) | Bantu | Swahili, Lingala, Zulu, Xhosa, Luganda… |
| [Kaufman PMED](https://github.com/lexibank/kaufmanpmed) | Mayan | Yucatec Maya, K'iche'… |
| [Tuled](https://github.com/lexibank/tuled) | Tupian / Guaraní | Guaraní |
| [Sidwell Vietic](https://github.com/lexibank/sidwellvietic) | Vietic | Vietnamese |
| [Dunn Aslian](https://github.com/lexibank/dunnaslian) | Austroasiatic | Khmer–Mon pair |
| [Crossandean](https://github.com/lexibank/crossandean) | Andean | Quechua, Aymara |
| [Uto-Aztecan](https://github.com/lexibank/utoaztecan) | Uto-Aztecan | Nahuatl |
| [Constenlac Chibchan](https://github.com/lexibank/constenlachibchan) *(calibration)* | Chibchan | (calibration pairs only) |

Calibration-only datasets contribute ASJP training pairs but currently contain no languages in the 283-language graph.

### Genetic similarity — ASJP fallback

**Source:** [ASJP v21](https://github.com/lexibank/asjp)

Used when no cognate pair exists in any dataset above. ASJP edit distances are calibrated against the cognate datasets: `slope × raw + genus_offset + intercept`.

The fallback is restricted to authorized pairs — unrestricted cross-genus ASJP is excluded because random syllable overlap inflates scores for unrelated languages.

**Authorized pairs:**
- Same WALS genus (e.g. two Romance languages, two Turkic languages)
- Cross-genus exceptions:

| Language | Authorized genera |
|----------|------------------|
| Haitian Creole | Romance (French lexifier) |
| Tok Pisin | Germanic (English-based pidgin) |
| Esperanto | Romance, Germanic, Slavic |
| Maltese | Romance (~50% Italian/Sicilian loanwords) |
| Coptic | Semitic (Afro-Asiatic intra-family) |
| Hausa | Semitic (Afro-Asiatic intra-family) |
| Somali | Semitic (Afro-Asiatic intra-family) |
| Tamazight, Kabyle, Tachelhit | Semitic (Afro-Asiatic intra-family) |
| Beja | Semitic + Lowland East Cushitic |
| Tibetan | Chinese, Burmese-Lolo (Sino-Tibetan intra-family) |
| Tlingit | Athapaskan (AET family) |

### Contact / loanword scores

Source: Wiktionary etymology data via kaikki.org. Score = `count(top-10k target-language words borrowed from source) / 10000`.

No frequency filter — with flat counts each word contributes ±1/10000, making high-frequency misattributions negligible.

- **~40 languages** covered by wordfreq: direct frequency-weighted scores.
- **Remaining majority**: calibrated via per-source OLS regression trained on the wordfreq-covered set (global R²=0.67). Languages with fewer than 20 documented borrowings are excluded.

Known limitation: per-source slopes are averages over the training languages. A source whose training set is dominated by heavy borrowers (e.g. Arabic via Persian/Turkish/Urdu, Sanskrit via Hindi/Bengali) will have an inflated slope and overestimate that source's role in languages where it was only a peripheral donor.

---

## Grammar similarity

**Formula:** best-source — `max(sim × level/5)` over portfolio languages.

One close relative is enough; grammar transfer doesn't stack like vocabulary.

### Typological data — [WALS v2020.4](https://github.com/cldf-datasets/wals)

Up to ~192 features per language pair. Sparse coverage is handled by alpha blending:

```
sim = alpha × raw_sim + (1 − alpha) × prototype_sim
alpha = min(shared_features / 20, 1.0)
```

At 0 shared features the genus prototype dominates entirely; at 20+ features raw WALS data is used as-is. The prototype for each language is the plurality-vote of well-attested genus members.

**ISO code patches** — three languages present in WALS under non-standard codes:

| Language | Wrong ISO | Correct ISO | WALS features |
|----------|-----------|-------------|---------------|
| Kurdish (Sorani) | kur | ckb | 60 |
| Pashto | pus | pst | 69 |
| Persian | fas | pes | 147 |

### Manual WALS profiles

48 languages absent from or poorly covered by WALS v2020.4 have been given manually curated profiles (~18 features each), baked into the bundle at generation time. Primarily historical varieties where WALS has no entry; a few are living languages corrected against a wrong prototype.

| Family | Languages |
|--------|-----------|
| IE — Italic historical | Latin, Oscan, Umbrian |
| IE — Celtic historical | Gaulish, Old Irish, Middle Welsh, Middle Breton |
| IE — Hellenic historical | Ancient Greek, Mycenaean Greek |
| IE — Germanic historical | Gothic, Old English, Old High German, Middle High German, Old Norse, Middle Dutch, Anglo-Norman |
| IE — Romance historical | Old French, Old Spanish, Old Occitan |
| IE — Indic historical | Sanskrit, Pali, Tocharian A, Tocharian B |
| IE — Armenian historical | Classical Armenian |
| IE — Iranian historical | Old Persian, Sogdian, Manichaean Middle Persian |
| IE — Baltic historical | Old Prussian |
| IE — Slavic historical | Old Russian |
| Anatolian | Hittite |
| Semitic historical | Akkadian, Ge'ez, Classical Syriac, Ugaritic, Phoenician, Old South Arabian (Yemeni) |
| Sino-Tibetan historical | Old Chinese, Old Tibetan |
| Turkic historical | Old Uyghur |
| East Asian historical | Old Japanese, Middle Korean |
| Paleo-European isolates | Etruscan, Elamite, Sumerian |
| Mesoamerican | Nahuatl |
| Constructed | Esperanto |
| Living (prototype correction) | North Azerbaijani (corrected against South Azerbaijani prototype) |

ISO codes for the 48 curated languages:
`lat san nci epo ett hit sux elx akk azj osc xum xtg grc gmy xcl got pli xto txb gez xno non goh ang och phn syc uga ayh peo sga gmh dum prg xct osp fro pro orv wlm xbm sog xmn oui okm ojp obr`

---

## Phonology similarity

**Formula:** coverage — fraction of the target's phoneme inventory already present in the portfolio union.

Portfolio languages at level ≥ 2 contribute their phoneme inventory to the known set.

**Source:** [PHOIBLE v2.0.1](https://github.com/cldf-datasets/phoible) — multiple inventories per language aggregated by union.

**Fallbacks:**
1. If the target has no PHOIBLE entry, its genus majority-vote prototype is used (a phoneme is included if it appears in >50% of genus members with PHOIBLE data).
2. If neither a real inventory nor a genus prototype exists, phonology returns a neutral score of 0.5.

---

## Script accessibility

**Formula:** `max(access_score)` over the language's listed scripts.

Multi-script languages (e.g. Mongolian Cyrillic + Traditional, Kazakh Latin + Cyrillic) are scored on whichever script the learner already knows best.

`access_score` is 1.0 if the learner's portfolio implies familiarity with the script, otherwise 0. A separate logographic penalty applies for character-based systems (Chinese characters, Japanese kanji).

**Source:** `data/scripts.yaml` — manually curated. Fields: `name`, `type` (alphabet / abjad / abugida / syllabary / logographic / featural / mixed), `direction`, `difficulty` (1–5), `family`, `notes`. Missing entries default to `[latin]`.
