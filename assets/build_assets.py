"""
Regenerates every hand-designed SVG in this folder from real content (bio
facts, skill percentages, project data) pulled from the portfolio site --
nothing here is templated boilerplate. Run after editing the data tables
below, or after fetching fresh fonts.

syne-bold.b64 / jbm-medium.b64 aren't committed (binary font data has no
business in git history). Regenerate them first:

  curl -sS -o syne-bold.woff2 "https://fonts.gstatic.com/s/syne/v24/8vIH7w4qzmVxm2BL9A.woff2"
  curl -sS -o jbm-medium.woff2 "https://fonts.gstatic.com/s/jetbrainsmono/v24/tDbv2o-flEEny0FZhsfKu5WU4zr3E_BX0PnT8RD8yKwBNntkaToggR7BYRbKPxDcwg.woff2"
  base64 -w0 syne-bold.woff2 > syne-bold.b64
  base64 -w0 jbm-medium.woff2 > jbm-medium.b64

Text overflow (three times, in earlier versions of this script) came
from guessing pixel widths per character and getting the guess wrong --
the dossier credential chips (packed horizontally with a width formula
that undercounted), a card title ("AGENTIC AIRSPACE") hand-split with
\\n at a guessed breakpoint, and "Fact-Check Overlay" still overflowing
at a 0.72em/char Syne estimate that measured as "fitting" by under 5px.
Fixed at the root with wrap_words() below: JetBrains Mono is genuinely
monospace (0.6em/char is its documented advance width, not a guess),
Syne's bold uppercase width is now estimated at 0.85em/char, and
wrap_words() asserts every line still fits after wrapping instead of
trusting the estimate blindly. Every card is now built through one
function (draw_card) that wraps against the card's real available width
instead of hand-picking line breaks, and asserts content fits vertically
at build time instead of relying on eyeballing a screenshot.

Project and research cards are individual SVG files (project-NN.svg,
research-NN.svg), not one combined grid image -- a single combined image
can only carry one link, so every card used to open the raw SVG on click
instead of the project. README.md wraps each in its own <a href>.
"""
import html

SYNE = open("syne-bold.b64", encoding="utf-8").read().strip()
JBM = open("jbm-medium.b64", encoding="utf-8").read().strip()

FONTS_CSS = f"""
      @font-face {{ font-family: 'SyneB'; font-weight: 800; src: url(data:font/woff2;base64,{SYNE}) format('woff2'); }}
      @font-face {{ font-family: 'JBM'; font-weight: 500; src: url(data:font/woff2;base64,{JBM}) format('woff2'); }}
"""

BASE_CSS = """
      .bg { fill: #0d0f1a; }
      .card { fill: #0f111d; stroke: #1e2235; stroke-width: 1; }
      .title { font-family: 'SyneB','Trebuchet MS',sans-serif; font-weight: 800; fill: #e8d08a; }
      .body { font-family: 'JBM',monospace; font-weight: 500; fill: #a0aac4; }
      .label { font-family: 'JBM',monospace; font-weight: 500; fill: #e8eaf2; }
      .idx { font-family: 'JBM',monospace; font-weight: 500; fill: #6b7a99; letter-spacing: 2px; }
      .tag { font-family: 'JBM',monospace; font-weight: 500; fill: #a78bfa; letter-spacing: 0.5px; }
      .pct { font-family: 'JBM',monospace; font-weight: 500; fill: #c9a84c; }
      .stat { font-family: 'SyneB','Trebuchet MS',sans-serif; font-weight: 800; }
      .dot { animation: pulse 2.2s ease-in-out infinite; transform-origin: center; }
      @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
      .barfill { animation: grow 1.4s ease-out both; }
      @keyframes grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
"""


def svg_open(w, h, extra_css="", extra_defs=""):
    return f"""<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
{FONTS_CSS}
{BASE_CSS}
{extra_css}
    </style>
{extra_defs}
  </defs>
  <rect class="bg" width="{w}" height="{h}"/>
"""


def esc(s):
    return html.escape(s, quote=False)


# JetBrains Mono's advance width is documented/exact at 0.6em per glyph --
# not a guess. Syne's bold uppercase average was first estimated at
# 0.72em/char and that was STILL wrong -- "Fact-Check Overlay" measured
# at 232.6px against a 237px budget under that estimate, comfortably
# "fit" by the math, and visibly overflowed the real card anyway. Real
# rendered width for a bold uppercase-heavy display face runs wider than
# a single average suggests. Bumped to 0.85em/char, and wrap_lines()
# below double-checks every line against that same figure after wrapping
# (not just during it), so a line that still doesn't fit fails the build
# with the actual offending text named, instead of shipping quietly.
CHAR_EM = {"jbm": 0.6, "syne": 0.85}


def wrap_words(text, max_width_px, font_size, font="jbm"):
    char_w = font_size * CHAR_EM[font]
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if not cur or len(cand) * char_w <= max_width_px:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)

    for line in lines:
        actual_w = len(line) * char_w
        if actual_w > max_width_px + 0.5:
            raise ValueError(
                f"wrap_words: line {line!r} estimated at {actual_w:.0f}px "
                f"still exceeds the {max_width_px:.0f}px budget after "
                f"wrapping (font={font}, size={font_size}) -- shorten it "
                f"or widen the card."
            )
    return lines


def draw_card(x, y, w, h, idx, title, desc, tags, color, delay=0.0):
    """One reusable card: dot + FILE index, title, wrapped description,
    tags. Raises if the wrapped content would overflow the card's own
    height, so a layout bug fails the build instead of shipping.

    No image or placeholder strip on purpose (dropped per direct
    feedback -- tried real screenshots first, which don't work at all in
    this architecture since an SVG loaded via <img src=...> is opaque to
    the browser and can't load its own external <image> refs; the
    placeholder-label strip that replaced them wasn't liked either).
    Just the real content, no top banner."""
    out = []
    out.append(f'  <g transform="translate({x},{y})">')
    out.append(f'    <rect class="card" width="{w}" height="{h}" rx="2"/>')

    pad = 18
    inner_w = w - pad * 2
    ty = 24
    out.append(f'    <circle class="dot" cx="{pad+8}" cy="{ty-4}" r="3" fill="{color}" style="animation-delay:-{delay}s"/>')
    out.append(f'    <text class="idx" x="{pad+20}" y="{ty}" style="font-size:11px">{esc(idx)}</text>')

    ty += 24
    title_lines = wrap_words(title, inner_w, 17, "syne")
    for tl in title_lines:
        out.append(f'    <text class="title" x="{pad}" y="{ty}" style="font-size:17px">{esc(tl)}</text>')
        ty += 21

    ty += 8
    desc_lines = wrap_words(desc, inner_w, 11, "jbm")
    for dl in desc_lines:
        out.append(f'    <text class="body" x="{pad}" y="{ty}" style="font-size:11px">{esc(dl)}</text>')
        ty += 16

    tag_y = h - 14
    if ty > tag_y - 6:
        raise ValueError(
            f"draw_card overflow: '{title}' content reaches y={ty} but tag "
            f"row starts at y={tag_y} inside a {h}px-tall card -- shorten "
            f"the description or grow the card."
        )
    out.append(f'    <text class="tag" x="{pad}" y="{tag_y}" style="font-size:9.5px">{esc(tags)}</text>')
    out.append("  </g>")
    return out


def build_card_file(path, w, h, idx, title, desc, tags, color):
    """One standalone card SVG, individually clickable when wrapped in its
    own <a href> in the README -- a single combined grid image can't have
    per-region links in plain markdown, which is why cards were unclickable
    (opening the raw SVG) before this split."""
    out = [svg_open(w, h)]
    out.extend(draw_card(0, 0, w, h, idx, title, desc, tags, color))
    out.append("</svg>\n")
    open(path, "w", encoding="utf-8").write("\n".join(out))
    print("wrote", path)


# ---------------------------------------------------------------- dossier.svg
def build_dossier():
    w, h = 1200, 330
    lines = [
        'I build agents that have to prove their reasoning, not just state a',
        'conclusion — a security scanner that has to tell a real sanitizer from a',
        'cosmetic one, a UX auditor that runs actual WCAG math instead of asking',
        'an LLM to guess a contrast ratio, a contradiction-finder that has to tell',
        '"sounds similar" apart from "actually conflicts."',
        '',
        'Every project below shipped with a real bug log — the dead ends, the',
        'wrong assumptions, the thing that broke on real data and why. That log',
        'is usually more interesting than the feature.',
    ]
    out = [svg_open(w, h)]
    y = 42
    for ln in lines:
        if ln == "":
            y += 14
            continue
        out.append(f'  <text class="body" x="24" y="{y}" style="font-size:16px">{esc(ln)}</text>')
        y += 27

    # Vertical list, not a horizontal packed row -- a fixed-width label
    # column plus a value column needs no per-string width guess at all,
    # which is what actually overflowed last time.
    y += 18
    creds = [
        ("DEGREE", "B.S. Artificial Intelligence — FAST-NUCES, Islamabad", "#c9a84c"),
        ("STANDING", "CGPA 3.62 / 4.0 — Dean's List ×5 · Rector's List", "#a78bfa"),
        ("ROLE", "Teaching Assistant — Agentic AI (Jan–Jun 2026)", "#c9a84c"),
        ("AVAILABLE", "June 2026", "#a78bfa"),
    ]
    for label, value, color in creds:
        out.append(f'  <circle class="dot" cx="30" cy="{y-4}" r="3" fill="{color}"/>')
        out.append(f'  <text class="idx" x="44" y="{y}" style="font-size:11px">{esc(label)}</text>')
        out.append(f'  <text class="label" x="180" y="{y}" style="font-size:13px">{esc(value)}</text>')
        y += 26

    out.append("</svg>\n")
    open("dossier.svg", "w", encoding="utf-8").write("\n".join(out))
    print("wrote dossier.svg")


# ------------------------------------------------------------------ skills.svg
def build_skills():
    w, h = 1200, 620
    categories = [
        ("CORE LANGUAGES", [
            ("Python", 95), ("HTML / CSS", 80), ("JavaScript", 78),
            ("C++", 72), ("SQL", 70), ("LaTeX", 65),
        ]),
        ("AI / ML FRAMEWORKS", [
            ("LangChain / LangGraph", 92), ("CrewAI", 90), ("PyTorch", 88),
            ("Hugging Face", 85), ("OpenCV / YOLO", 82), ("TensorFlow", 80), ("scikit-learn", 78),
        ]),
        ("AGENTIC & GENAI", [
            ("Multi-Agent Systems", 93), ("RAG Architecture", 90), ("ReAct / Reflexion / CoT", 88),
            ("Prompt Engineering", 88), ("MCP Tools", 85), ("Ollama / Local LLMs", 85), ("LLM Fine-tuning", 78),
        ]),
        ("TOOLS & INFRASTRUCTURE", [
            ("Git / GitHub", 90), ("FastAPI / Flask", 82), ("n8n / Gradio", 78),
            ("Docker", 75), ("MongoDB / MySQL", 72),
        ]),
    ]

    quadrants = [(24, 20), (612, 20), (24, 330), (612, 330)]
    colors = ["#c9a84c", "#a78bfa", "#c9a84c", "#a78bfa"]

    out = [svg_open(w, h)]
    for (qx, qy), (cat, items), color in zip(quadrants, categories, colors):
        out.append(f'  <rect class="card" x="{qx}" y="{qy}" width="564" height="290" rx="2"/>')
        out.append(f'  <text class="title" x="{qx+20}" y="{qy+34}" style="font-size:17px;letter-spacing:1px">{esc(cat)}</text>')
        ry = qy + 60
        bar_x = qx + 260
        bar_w = 230
        for name, pct in items:
            out.append(f'  <text class="label" x="{qx+20}" y="{ry+4}" style="font-size:13px">{esc(name)}</text>')
            out.append(f'  <rect x="{bar_x}" y="{ry-6}" width="{bar_w}" height="4" fill="#1e2235"/>')
            fw = bar_w * pct / 100
            out.append(f'  <rect class="barfill" x="{bar_x}" y="{ry-6}" width="{fw:.0f}" height="4" fill="{color}" style="transform-origin:{bar_x}px {ry-4}px"/>')
            out.append(f'  <text class="pct" x="{bar_x+bar_w+14}" y="{ry+4}" style="font-size:12px">{pct}%</text>')
            ry += 31
    out.append("</svg>\n")
    open("skills.svg", "w", encoding="utf-8").write("\n".join(out))
    print("wrote skills.svg")


# -------------------------------------------------------- project-NN.svg
# Link priority per project, as requested: real repo first, else the live
# deployment, else (for DetectifAI, which has neither) the real demo
# video -- falling further back to the portfolio only when nothing more
# specific exists.
def build_projects_all():
    cards = [
        dict(idx="FILE 01", title="Aura — AI UX Auditor",
             desc="Real WCAG contrast math on sampled pixels, a real saliency model for attention — one AI call for the one thing code can't judge.",
             tags="NEXT.JS · CONVEX · GEMINI", color="#c9a84c",
             link="https://github.com/blacksinisterx/Ai-UX-Auditor"),
        dict(idx="FILE 02", title="Exploit-Path Tracer",
             desc="Traces multi-hop taint paths and tells a real sanitizer apart from one that only looks like it.",
             tags="SEMGREP · LANGGRAPH · GROQ", color="#a78bfa",
             link="https://github.com/blacksinisterx/Exploit-Path-Tracer"),
        dict(idx="FILE 03", title="Deposition Contradiction Finder",
             desc="Catches real contradictions in witness testimony, and correctly dismisses the ones that only sound like a match.",
             tags="SUPABASE · LANGGRAPH · GROQ", color="#c9a84c",
             link="https://github.com/blacksinisterx/Deposition-Contradiction-Finder"),
        dict(idx="FILE 04", title="DetectifAI",
             desc="Real-time CCTV threat detection — weapons, intrusions, behavioral anomalies. YOLO + CLIP vision-language + FaceNet identity tracking.",
             tags="YOLO · CLIP · FASTAPI", color="#a78bfa",
             link="https://drive.google.com/file/d/1ZpO-nzMJUw8zg00oiZCB-ZGMa06_vxou/view"),
        dict(idx="FILE 05", title="Multi-Tenant Agentic RAG",
             desc="Tenant isolation, ACL enforcement, PII masking, prompt-injection detection. Passed red-team evaluation.",
             tags="LANGCHAIN · CREWAI", color="#c9a84c",
             link="https://github.com/blacksinisterx/Multi-Tenant-Agentic-RAG-System"),
        dict(idx="FILE 06", title="CrisSim — Disaster Response",
             desc="Heterogeneous agents simulating earthquake response — medic and drone coordination, benchmarking ReAct, Reflexion, and CoT.",
             tags="LANGGRAPH · REACT", color="#a78bfa",
             link="https://github.com/blacksinisterx/CrisSim-Multi-Agent-Simulation"),
        dict(idx="FILE 07", title="Agentic Airspace Copilot",
             desc="Live flight-anomaly detection on real OpenSky API data. CrewAI + LangGraph orchestration with MCP tool integration.",
             tags="CREWAI · MCP", color="#c9a84c",
             link="https://github.com/sincera315/Assignment3_Agentic_AI_N8N"),
        dict(idx="FILE 08", title="AI Video Narrator",
             desc="Local text-to-speech and captions, entirely in-browser as WASM. Nothing leaves the tab.",
             tags="KOKORO · FFMPEG.WASM", color="#a78bfa",
             link="https://github.com/blacksinisterx/Ai-Video-Narrator"),
        dict(idx="FILE 09", title="Fact-Check Overlay",
             desc="Select a claim, get a sourced verdict — both sides shown if the claim is genuinely contested.",
             tags="GROQ · TAVILY", color="#c9a84c",
             link="https://github.com/blacksinisterx/Fact-Checker"),
        dict(idx="FILE 10", title="Clickbait Decoder",
             desc="Names the manipulation tactic in a headline and scores it, before you spend the click.",
             tags="GROQ", color="#a78bfa",
             link="https://github.com/blacksinisterx/Clickbait-Decoder"),
        dict(idx="FILE 11", title="AI Slop Blocker",
             desc="Removes AI-generated posts from a feed as you scroll, without breaking the page's own React state.",
             tags="GROQ VISION", color="#c9a84c",
             link="https://github.com/blacksinisterx/Ai-Slop-Blocker"),
    ]

    cw, ch = 273, 210
    for i, c in enumerate(cards, start=1):
        build_card_file(f"project-{i:02d}.svg", cw, ch, c["idx"], c["title"], c["desc"], c["tags"], c["color"])
    return cards


# ------------------------------------------------------- research-NN.svg
def draw_research_card(w, h, idx, title, stat, statdesc, desc, color):
    """Same shape as draw_card() (dot+idx, wrapped title, then a headline
    stat, statdesc and desc) but as its own function since research cards
    carry a stat line project cards don't. Same build-time overflow
    assertion as draw_card()."""
    pad = 20
    inner_w = w - pad * 2
    out = [f'  <rect class="card" width="{w}" height="{h}" rx="2"/>']
    out.append(f'  <circle class="dot" cx="22" cy="26" r="3.5" fill="{color}"/>')
    out.append(f'  <text class="idx" x="34" y="30" style="font-size:12px">{esc(idx)}</text>')

    ty = 58
    for tl in wrap_words(title, inner_w, 16.5, "syne"):
        out.append(f'  <text class="title" x="{pad}" y="{ty}" style="font-size:16.5px">{esc(tl)}</text>')
        ty += 21

    ty += 20
    out.append(f'  <text class="stat" x="{pad}" y="{ty}" style="font-size:24px" fill="{color}">{esc(stat)}</text>')
    ty += 20
    for sl in wrap_words(statdesc, inner_w, 10.5, "jbm"):
        out.append(f'  <text class="body" x="{pad}" y="{ty}" style="font-size:10.5px">{esc(sl)}</text>')
        ty += 14

    ty += 12
    for dl in wrap_words(desc, inner_w, 10.5, "jbm"):
        if ty > h - 10:
            raise ValueError(
                f"research card overflow: '{title}' content reaches y={ty} "
                f"in a {h}px-tall card -- shorten the description or grow "
                f"the card."
            )
        out.append(f'  <text class="body" x="{pad}" y="{ty}" style="font-size:10.5px;opacity:0.8">{esc(dl)}</text>')
        ty += 15
    return out


def build_research():
    items = [
        dict(idx="FILE R1", title="Security Audit of Agentic AI Frameworks", stat="0.90–1.00",
             statdesc="attack success rate, multi-agent systems, even in secured configs",
             desc="5 adversarial scenarios across LangChain, CrewAI, and multi-agent setups: prompt injection, tool injection, unauthorized execution, memory poisoning.",
             color="#c9a84c", link="https://github.com/blacksinisterx/Agentic-AI-Safety-Audit"),
        dict(idx="FILE R2", title="FAST Federated Unlearning", stat="95.02% → 0.0981",
             statdesc="backdoor attack success rate, zero false positives",
             desc="Extended the IEEE TNSE 2024 FAST framework across 3 attack types on 10 distributed clients, without full model retraining. 99% accuracy recovery.",
             color="#a78bfa", link="https://github.com/blacksinisterx/federated-unlearning-multi-attack-evaluation"),
        dict(idx="FILE R3", title="Multi-Turn AI Safety Benchmark", stat="2.5×",
             statdesc="more frequent context-accumulation attack success",
             desc="Local eval across Llama3-8B, Hermes3-8B, Qwen2.5-7B via JailbreakBench and TruthfulQA. Introduced CARI, an original context-accumulation risk metric.",
             color="#c9a84c", link="https://storm-bureau-portfolio.vercel.app/"),
        dict(idx="FILE R4", title="Seed-Free Data-to-Text Synthesis", stat="114.2%",
             statdesc="of fully-supervised baseline, zero-shot",
             desc="Zero-shot pipeline via Llama 3.1:8B across WebNLG, E2E, and WikiTableQuestions. Eliminates $5K–$50K of human annotation cost per dataset.",
             color="#a78bfa", link="https://storm-bureau-portfolio.vercel.app/"),
        dict(idx="FILE R5", title="CIFAR-100 CNN Architecture", stat="68.01% → 93.34%",
             statdesc="reproduced baseline vs. enhanced result",
             desc="Reproduced Yang et al. (2023), then enhanced with residual attention and SE blocks for a +25.33% accuracy gain over the original baseline.",
             color="#c9a84c", link="https://github.com/blacksinisterx/Artificial-Neural-Network-Project"),
    ]
    cw, ch = 376, 270
    for i, it in enumerate(items, start=1):
        path = f"research-{i:02d}.svg"
        out = [svg_open(cw, ch)]
        out.extend(draw_research_card(cw, ch, it["idx"], it["title"], it["stat"], it["statdesc"], it["desc"], it["color"]))
        out.append("</svg>\n")
        open(path, "w", encoding="utf-8").write("\n".join(out))
        print("wrote", path)
    return items


# --------------------------------------------------------------- headers
def build_header(num, title, out_path, dur=4.5):
    extra = f"""
      .hnum {{ font-family: 'JBM',monospace; font-weight: 500; font-size: 15px; fill: #c9a84c; letter-spacing: 2px; }}
      .htitle {{ font-family: 'SyneB','Trebuchet MS',sans-serif; font-weight: 800; font-size: 30px; fill: #e8eaf2; letter-spacing: 0.5px; }}
      .brk {{ stroke: #c9a84c; stroke-width: 2; fill: none; opacity: 0.85; }}
      .tick {{ stroke: #2a3050; stroke-width: 1; }}
      .pulse {{ animation: travel {dur}s linear infinite; }}
      @keyframes travel {{
        0%   {{ transform: translateX(-50px); opacity: 0; }}
        6%   {{ opacity: 1; }}
        94%  {{ opacity: 1; }}
        100% {{ transform: translateX(1250px); opacity: 0; }}
      }}
    """
    extra_defs = """
    <linearGradient id="pulseGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#c9a84c" stop-opacity="0"/>
      <stop offset="50%" stop-color="#e8d08a" stop-opacity="1"/>
      <stop offset="100%" stop-color="#a78bfa" stop-opacity="0"/>
    </linearGradient>
    """
    out = [svg_open(1200, 76, extra, extra_defs)]
    out.append('  <path class="brk" d="M 16 14 L 16 28 M 16 14 L 30 14"/>')
    out.append('  <path class="brk" d="M 1184 14 L 1184 28 M 1184 14 L 1170 14"/>')
    out.append(f'  <text class="hnum" x="64" y="34">MISSION-{num} ::</text>')
    out.append(f'  <text class="htitle" x="64" y="63">{esc(title)}</text>')
    out.append('  <line class="tick" x1="0" y1="75" x2="1200" y2="75"/>')
    out.append('  <rect class="pulse" x="0" y="73.5" width="50" height="2.5" fill="url(#pulseGrad)"/>')
    out.append("</svg>\n")
    open(out_path, "w", encoding="utf-8").write("\n".join(out))
    print("wrote", out_path)


# ------------------------------------------------------ light-mode variants
# GitHub's own theme-context pattern (already used for the snake animation
# below) is two static files switched by <picture>/<source media=...>, not
# a media query inside the SVG itself. Every dark asset in this repo --
# banner, headers, dossier, skills, project/research cards -- draws from
# exactly the same ~14 hex colors, in CSS classes AND in literal fill/
# stroke attributes, always the same string. That means a plain find/
# replace over an already-rendered dark file produces a correct light
# file without re-deriving any layout, and leaves the dark file (the one
# actually referenced by default in the README) byte-for-byte untouched.
LIGHT_MAP = {
    "#07080f": "#f6f2e4",  # banner bg (near-black)        -> parchment bg
    "#0d0f1a": "#f6f2e4",  # main bg                        -> parchment bg
    "#0f111d": "#fffdf7",  # card fill                      -> paper card
    "#1e2235": "#ddd3b0",  # card stroke / bar track        -> tan border
    "#e8d08a": "#7a5a12",  # title text (light gold)        -> deep gold-brown
    "#a0aac4": "#4a4636",  # body text (light slate)        -> warm charcoal
    "#e8eaf2": "#1c1810",  # label/heading text (near-white)-> near-black
    "#6b7a99": "#8a7f5e",  # idx text (slate-blue)          -> warm gray-brown
    "#a78bfa": "#6d46b8",  # purple accent                  -> deep purple
    "#c9a84c": "#a8873a",  # gold accent                    -> deep gold (matches snake-light)
    "#7c5cbf": "#9b7ee0",  # banner secondary purple        -> mid purple
    "#3d2d7a": "#ceb8f5",  # banner purple glow (dark bg)   -> pastel purple glow
    "#2a2010": "#f2e0a8",  # banner gold glow (dark bg)     -> pastel gold glow
    "#2a3050": "#d8cfb0",  # header tick/divider line       -> tan divider
}


# ------------------------------------------------------------ accent swap
# Gold was the primary/most-visible accent everywhere (title text, header
# numerals, the alternating odd-numbered cards, the banner's main sweep)
# and it wasn't reading as vivid enough against the near-black background
# -- direct feedback. Rather than hand-edit every one of the ~15 places
# gold/purple literals appear (BASE_CSS, each header's extra CSS, both
# card lists, dossier creds, skills quadrants, banner gradients), this
# swaps the two 3-shade families wherever they appear in an already-
# rendered file: gold's {primary, light, glow} triplet trades places with
# purple's {primary, secondary, glow} triplet. Purple/lavender becomes
# the prominent color, gold becomes the alternate. Runs on every dark
# file, including banner.svg/header-01..04.svg which have no generator
# function in this script (hand-built, edited in place).
# ponytail: only swaps these 6 known hex literals -- a new accent color
# added later needs its own swap pair added to ACCENT_SWAP_PAIRS below.
import re

ACCENT_SWAP_PAIRS = [("c9a84c", "a78bfa"), ("e8d08a", "7c5cbf"), ("2a2010", "3d2d7a")]
ACCENT_SWAP = {}
for _a, _b in ACCENT_SWAP_PAIRS:
    ACCENT_SWAP[_a] = _b
    ACCENT_SWAP[_b] = _a
_accent_re = re.compile("|".join(ACCENT_SWAP.keys()))


def recolor_accents(path):
    text = open(path, encoding="utf-8").read()
    text = _accent_re.sub(lambda m: ACCENT_SWAP[m.group(0)], text)
    open(path, "w", encoding="utf-8").write(text)
    print("recolored", path)


def make_light_variant(path):
    text = open(path, encoding="utf-8").read()
    for dark, light in LIGHT_MAP.items():
        text = text.replace(dark, light)
    light_path = path.replace(".svg", "-light.svg")
    open(light_path, "w", encoding="utf-8").write(text)
    print("wrote", light_path)


build_dossier()
build_skills()
build_projects_all()
build_research()
build_header("05", "SIGNAL TRACE", "header-05.svg")
build_header("06", "SECURE CHANNEL", "header-06.svg")

ASSET_FILES = (
    ["banner.svg"]
    + [f"header-{n:02d}.svg" for n in range(1, 7)]
    + ["dossier.svg", "skills.svg"]
    + [f"project-{n:02d}.svg" for n in range(1, 12)]
    + [f"research-{n:02d}.svg" for n in range(1, 6)]
)
for f in ASSET_FILES:
    recolor_accents(f)
for f in ASSET_FILES:
    make_light_variant(f)
