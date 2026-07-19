# BrowserPilot Generative UI — Design Plan

## The brief (grounded in the subject)

**Subject:** dashboards generated from *scraped websites*. The tool takes messy, hostile web pages and turns them into clean, structured, trustworthy data.
**The page's one job:** make that generated dashboard feel calm, credible, and **worth sharing** — because the shared dashboard is the growth flywheel, not decoration.
**Audience:** developers, data engineers, competitive-intel people. They trust *precision*, not flourish.

**What's wrong now** (audit + issue #39): the light theme is harsh — pure-white `#FFFFFF` background, saturated blue `hsl(217 91% 60%)` primary, loud gold `hsl(43 96% 56%)` accent, near-black ink. Motion is busy (hover scale 1.03 + glow + spring pop-ins). Two radius systems and two shadow systems coexist; some CSS is duplicated and invalid. The layout is a desktop tri-pane with *mobile fallbacks*, not mobile-first. ~253 `console.log`s ship to production. The **dark theme, by contrast, is already calm and premium** — so the fix is to bring that discipline to light mode and unify everything.

## Chosen direction: **Signal (dark-first)** ✅

Selected 2026-07-08. The app **defaults to the (already-strong) dark theme** — near-black surfaces `#050608`, soft sky/indigo accent `#7DD3FC`, tasteful *ambient* depth (not per-hover springs). Light "Paper" mode stays available via the toggle and gets de-harshened, but dark is the identity. This leverages the existing premium dark theme instead of rebuilding light mode, so it's lower-risk and faster to a shareable, sleek result. Everything below (mono/tabular numbers, one accent, materialize reveal, mobile-first, share view) applies — read the color section as "polish + unify the dark theme; make it the default."

## Design thesis: **Quiet Instrument**

The product is a measurement instrument for the web. The UI should read like one: precise, calm, data foregrounded, chrome receding. Restraint everywhere — spend boldness in exactly one place (the dashboard *materializing*). "Softer," done right, means *quieter and more confident*, not just lighter. In dark-first, the ambient glow is the depth cue — kept subtle and reserved for the accent, never scattered across hovers.

## Token system

### Color — "Paper" (light) and "Ink" (dark)

Light (**Paper**):
| Token | Hex | Role |
|---|---|---|
| Paper | `#FAFBFC` | app background (cool off-white, **not** pure white) |
| Surface | `#FFFFFF` | cards, raised on hairlines |
| Ink | `#1B2432` | text (desaturated navy — softer than pure black) |
| Muted ink | `#5B6675` | secondary text, labels |
| Hairline | `#E6EAF0` | borders, dividers |
| Accent | `#3E5DE7` | interaction — a considered cobalt-indigo, deliberately **not** the saturated default blue |

Semantic (used **only** for data meaning, kept muted):
- Positive `#1F9D6B` (cheapest / up-is-good) · Attention `#B45C3C` (priciest — a warm low-sat clay that replaces the loud gold).

Dark (**Ink**): keep the existing calm dark theme; align it to the same single accent + hairline discipline. **Remove the decorative gold accent entirely** — one interaction accent, semantics reserved for data.

### Type

- **Display + UI:** Geist (fallback Inter) — a technical grotesk built for product interfaces.
- **Data face — the type signature:** **Geist Mono / tabular figures** for every number (prices, metrics, table cells, axes). Numbers *are* the product; a mono, tabular face makes columns align and reads unmistakably as "data." This is a choice the subject demands, not a default.
- Scale: restrained — 32 / 22 / 16 / 14 / 13; tight display tracking, generous body leading.

### Layout

- **Mobile-first.** Phone: a single stacked column — metric row → chart → table — full-width, thumb-reachable, sections collapsible. Desktop: the tri-pane, but quieter (hairline dividers, more whitespace, a recessive sidebar). Designed for the phone, enhanced for the desktop — not the reverse.
- **Share view:** a clean, dashboard-only mode (no chat / dev chrome) so a screenshot or link is presentable.

### Signature — **the materialize reveal**

As the dashboard builds, components stagger in — a calm ~90–120ms stagger, 8px rise + fade, orchestrated **once** on load. It embodies the product's magic moment ("watch the dashboard build itself" — also the viral demo) and *replaces* the current scattered hover glows and spring pops. `prefers-reduced-motion` disables it. Paired with a small, tasteful **"built with BrowserPilot"** wordmark on shared dashboards — the flywheel, made quiet.

## Changes, mapped to the problems

1. **Light theme → Paper palette** (off-white, ink, single indigo accent; gold removed). [#39]
2. **Unify tokens** — one radius scale, one shadow scale; delete the duplicated + invalid CSS.
3. **Motion** — remove hover scale/glow/spring; add the single materialize reveal; respect reduced-motion.
4. **Mobile-first layout** — intentional phone view; desktop calmer.
5. **Data typography** — mono/tabular numerals across metric cards, charts, tables.
6. **Share view + wordmark** — make the artifact shareable.
7. **Hygiene** — strip `console.log`s; replace off-token colors (`text-green-500`, inline hexes) with tokens.

## Self-critique — is this a choice, or a default?

The three AI-design defaults are cream+serif+terracotta, near-black+acid-accent, and broadsheet hairline columns. This is none of them. The **distinctive, subject-derived moves are the mono/tabular data face and the materialize reveal** — both fall out of "this tool turns web pages into data." The accent is a deliberate indigo, chosen *against* the reflexive saturated blue. Boldness is spent in one place (the reveal); everything else stays quiet. Risk taken and justified: committing the whole numeric layer to a mono face in a shadcn app most people would set in Inter.

## Scope / phases

- **P1 — Tokens:** rewrite `index.css` light theme, unify radius/shadow, delete dead/invalid CSS.
- **P2 — Type:** wire Geist + Geist Mono; tabular numerals on all data.
- **P3 — Components:** calm MetricCard / chart / table; the materialize reveal.
- **P4 — Layout:** mobile-first restructure + the clean share view + wordmark.
- **Cleanup:** console.logs, off-token colors.

**Acceptance:** light theme reads calm and matches the dark theme's quality; the dashboard is genuinely usable and attractive on a phone; one token system; a shared dashboard looks like something you'd *want* to share.
