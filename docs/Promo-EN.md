# Promo Material (English) – Förder-Radar (Grant Agent)

> For: FLASH jury (EN versions), Demo Day visitors, international partners,
> open-source contributors. All figures are real (as of 2026-08-12):
> **97 programmes, 9 funding categories, open source (MIT), local &
> privacy-friendly.** Project principle: honest, no overstatement.

---

## 1. Elevator Pitch (30 seconds)

> "Every week, researchers answer two questions by hand: *Which funding fits
> me?* and *When is the deadline?* Förder-Radar turns this into a personal
> brief: your most realistic next opportunities — with reasoning, budget, and
> a deadline countdown. No expensive subscription database: it uses open,
> official sources (DFG, ERC, national, regional, foundations) and runs
> locally — privacy-friendly, no cloud required. The prototype is open
> source, covers 97 programmes across nine funding categories, and connects
> to any AI assistant via the Model Context Protocol (MCP). First pilot: our
> own faculty at Philipps-Universität Marburg."

---

## 2. Taglines (English)

1. **"Your next deadline. Not the next database."** *(main claim)*
2. "Profile + deadline instead of an overflow of options."
3. "80 pots. One brief. No missed deadline."
4. "Find funding before the deadline finds you."
5. "The personal funding radar for research."
6. "Open data. Open source. Open future."
7. "What PIVOT does — can be done locally, too." *(internal only, too pointed)*

---

## 3. One-Pager (DIN A4, English, jury handout)

### Förder-Radar – Grant Intelligence
*The personal grant assistant for Philipps-Universität*

**The problem**
Researchers spend hours every week on two questions: "Which funding fits me?"
and "When is the deadline?" Answers are scattered across portals, emails, and
calendars. Missed deadlines mean missed funding — silently.

**The solution**
A small, self-hostable assistant that condenses official, freely licensed
sources (DFG, ERC, national, regional, foundations) into a personal brief via
an agent loop — intake, search, alert. Top matches with reasoning and budget,
the next deadline in days, timely warnings.

**What sets it apart**

| | |
|---|---|
| **Open** | Open source (MIT), code + catalog on GitHub, contribute via merge request |
| **Privacy-friendly** | Runs locally, no cloud requirement, DSGVO-ready consent for profiles |
| **Standards-based** | Model Context Protocol (MCP) — pluggable into any AI assistant |
| **Honest** | Official sources only, every deadline with a "as of" date, scores as orientation |
| **Fact-based** | 97 programmes, 9 categories, 181 tests, 100 % test coverage |

**The value**
- Less searching and coordinating
- Fewer missed deadlines
- A clear basis for decisions

**The path**
A pilot in our own faculty — live within weeks, delivering real metrics as the
basis for a recurring, paid use. First Marburg, then transferable to other
universities.

**Contributions welcome:** maintaining sources, sharpening matching rules,
joining the first pilot.

---

## 4. Social Media (English)

### 4.1 LinkedIn (main post, ~1200 chars)

> **Deadlines are invisible — until they expire.** 🎯
>
> Every week, researchers answer two questions by hand: "Which funding fits
> me?" — and "When is the deadline?" The answers are scattered across
> portals, emails, and calendars. Missed deadline = missed funding.
>
> That's why we built **Förder-Radar**: a personal grant assistant that
> condenses official, open sources (DFG, ERC, national, regional,
> foundations) into a weekly brief — top matches with reasoning, budget, and
> a deadline countdown.
>
> What matters to us:
> - 🧩 **Open source** (MIT) — code and catalog are public, contribute via merge request
> - 🔒 **Privacy-friendly** — runs locally, DSGVO-ready, no cloud requirement
> - 🤖 **Standards-based** — Model Context Protocol (MCP), pluggable into any AI
> - 📊 **Facts over hype** — 97 programmes, 9 categories, 100 % test coverage
>
> First pilot: our own faculty at Philipps-Universität Marburg. Interested in
> a joint pilot or in maintaining sources? Reach out — or just contribute:
> the catalog is open. 💡
>
> #GrantRadar #FLASH #OpenSource #MCP #ResearchFunding #Science #Marburg

### 4.2 X / Threads (short)

> Your next deadline. Not the next database. 📡
>
> Förder-Radar condenses open sources (DFG, ERC, national, regional,
> foundations) into a personal brief: top matches + deadline countdown,
> local & privacy-friendly.
>
> Open source (MIT) · MCP-based · 97 programmes · first pilot at the
> University of Marburg. Join us! 💡
>
> #GrantRadar #FLASH #OpenSource #MCP #Research

### 4.3 LinkedIn (teaser, short)

> "Find funding before the deadline finds you." 📡
> Förder-Radar — our FLASH project at Philipps-Universität Marburg.
> Open sources, local operation, MCP standard. Details to follow — questions
> welcome in the comments.

---

## 5. Poster / Flyer (English, Demo Day)

### Header
**FÖRDER-RADAR** · *Your next deadline. Not the next database.*

### 3 blocks (left → right)

**Problem** 😰
- "Which funding fits me?"
- "When is the deadline?"
- Answers scattered across portals, emails, calendars

**Solution** 📡
- A personal brief instead of a flood of results
- Top matches with reasoning + budget
- Deadline countdown + timely warnings

**Why us** 💡
- Open source (MIT) · local · privacy-friendly
- MCP standard → pluggable into any AI
- 97 programmes · 9 categories · 181 tests

### Footer
> **Live demo:** 3 profiles · 1 screen · 2 minutes
> **Join us:** github.com/tobias-weiss-ai-xr/grant-intelligence
> Förder-Radar · FLASH 2026 · Philipps-Universität Marburg

---

## 6. Live Demo Script (2 minutes, Demo Day, EN)

| Time | Action | Speaker |
|------|--------|---------|
| 0:00–0:15 | Show profile (`profiles.json`) | "This is a real pilot profile: postdoc, AI research, ORCID linked, consent given." |
| 0:15–0:45 | `brief.py --felder "Artificial Intelligence" --karriere postdoc` | "One command — and the weekly brief is there: top matches, reasoning, deadlines in days, warnings." |
| 0:45–1:15 | UI `uvicorn app:app` (browser) | "The same logic as a single page — no signup, no cloud, all local." |
| 1:15–1:45 | `match_best(...)` via MCP (demo agent) | "And because everything is MCP-based, any AI assistant can directly ask: 'Which funding fits me?'" |
| 1:45–2:00 | State catalog number | "97 programmes across nine categories — DFG, ERC, national, regional, foundations, EU, industry, international. All from official sources, every deadline with an 'as of' date." |

**Fallback if the demo fails:** one-pager (§3) + screenshot at hand.

---

## 7. Logo / Visual Language (EN notes)

- **Colors:** Petrol/Dark blue (#0F4C5C) + accent orange (#E36414) — "radar + warning signal".
- **Motif:** Radar screen with a deadline number in the center (e.g., "42 days").
- **Text combo:** "Förder-Radar" + claim "Your next deadline."
- **Screenshot candidates:** weekly brief (Markdown) and the single-screen UI.

---

## 8. One-Sentence Variants (newsletter, EN)

- **Short (15 words):** "Förder-Radar: open sources + your profile → your next
  grant opportunities with a deadline countdown — local, open, privacy-friendly."
- **With context (30 words):** "Our FLASH project Förder-Radar condenses
  official funding data (DFG, ERC, national, regional, foundations) into a
  personal weekly brief — open source, MCP-based, pilot in our own faculty."

---

## 9. CTA line (reusable)

> **Join us:** https://github.com/tobias-weiss-ai-xr/grant-intelligence
> · add your profile via merge request · maintain sources · start a pilot
