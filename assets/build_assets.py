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

Text overflow (twice, in earlier versions of this script) came from
guessing pixel widths per character and getting the guess wrong -- once
on the dossier credential chips (packed horizontally with a width formula
that undercounted), once on a card title ("AGENTIC AIRSPACE") that was
hand-split with \\n at a guessed breakpoint that didn't actually fit.
Fixed at the root with wrap_words() below: JetBrains Mono is genuinely
monospace (0.6em/char is its documented advance width, not a guess), and
Syne's bold uppercase width is estimated generously (0.72em/char) so the
wrapper wraps a little early rather than risk overflowing. Every card is
now built through one function (draw_card) that wraps against the card's
real available width instead of hand-picking line breaks, and asserts
content fits vertically at build time instead of relying on eyeballing a
screenshot.
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
# not a guess. Syne's bold uppercase average is estimated generously at
# 0.72em/char (real value varies per letter; this errs toward wrapping
# early rather than overflowing).
CHAR_EM = {"jbm": 0.6, "syne": 0.72}


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


# ------------------------------------------------------------- projects-all.svg
def build_projects_all():
    """All 11 Operation Log projects through the same draw_card() --
    replaces the old HTML table + projects-ops.svg + projects-secondary.svg,
    which were three different hand-coded layouts (the actual source of
    the "these don't match" complaint)."""
    cards = [
        dict(idx="FILE 01", title="Aura — AI UX Auditor",
             desc="Real WCAG contrast math on sampled pixels, a real saliency model for attention — one AI call for the one thing code can't judge.",
             tags="NEXT.JS · CONVEX · GEMINI", color="#c9a84c"),
        dict(idx="FILE 02", title="Exploit-Path Tracer",
             desc="Traces multi-hop taint paths and tells a real sanitizer apart from one that only looks like it.",
             tags="SEMGREP · LANGGRAPH · GROQ", color="#a78bfa"),
        dict(idx="FILE 03", title="Deposition Contradiction Finder",
             desc="Catches real contradictions in witness testimony, and correctly dismisses the ones that only sound like a match.",
             tags="SUPABASE · LANGGRAPH · GROQ", color="#c9a84c"),
        dict(idx="FILE 04", title="DetectifAI",
             desc="Real-time CCTV threat detection — weapons, intrusions, behavioral anomalies. YOLO + CLIP vision-language + FaceNet identity tracking.",
             tags="YOLO · CLIP · FASTAPI", color="#a78bfa"),
        dict(idx="FILE 05", title="Multi-Tenant Agentic RAG",
             desc="Tenant isolation, ACL enforcement, PII masking, prompt-injection detection. Passed red-team evaluation.",
             tags="LANGCHAIN · CREWAI", color="#c9a84c"),
        dict(idx="FILE 06", title="CrisSim — Disaster Response",
             desc="Heterogeneous agents simulating earthquake response, medic and drone coordination. Benchmarks ReAct, Reflexion, and Chain-of-Thought.",
             tags="LANGGRAPH · REACT", color="#a78bfa"),
        dict(idx="FILE 07", title="Agentic Airspace Copilot",
             desc="Live flight-anomaly detection on real OpenSky API data. CrewAI + LangGraph orchestration with MCP tool integration.",
             tags="CREWAI · MCP", color="#c9a84c"),
        dict(idx="FILE 08", title="AI Video Narrator",
             desc="Local text-to-speech and captions, entirely in-browser as WASM. Nothing leaves the tab.",
             tags="KOKORO · FFMPEG.WASM", color="#a78bfa"),
        dict(idx="FILE 09", title="Fact-Check Overlay",
             desc="Select a claim, get a sourced verdict — both sides shown if the claim is genuinely contested.",
             tags="GROQ · TAVILY", color="#c9a84c"),
        dict(idx="FILE 10", title="Clickbait Decoder",
             desc="Names the manipulation tactic in a headline and scores it, before you spend the click.",
             tags="GROQ", color="#a78bfa"),
        dict(idx="FILE 11", title="AI Slop Blocker",
             desc="Removes AI-generated posts from a feed as you scroll, without breaking the page's own React state.",
             tags="GROQ VISION", color="#c9a84c"),
    ]

    cw, gap, cols, margin = 273, 12, 4, 24
    card_h = 210
    rows = -(-len(cards) // cols)
    w = margin * 2 + cw * cols + gap * (cols - 1)
    h = margin + rows * card_h + (rows - 1) * gap + margin

    out = [svg_open(w, h)]
    for i, c in enumerate(cards):
        col, row = i % cols, i // cols
        x = margin + col * (cw + gap)
        y = margin + row * (card_h + gap)
        out.extend(draw_card(
            x, y, cw, card_h, c["idx"], c["title"], c["desc"], c["tags"], c["color"],
            delay=i * 0.3,
        ))
    out.append("</svg>\n")
    open("projects-all.svg", "w", encoding="utf-8").write("\n".join(out))
    print(f"wrote projects-all.svg ({w}x{h})")


# -------------------------------------------------------------- research.svg
def build_research():
    w, h = 1200, 580
    items = [
        ("FILE R1", "Security Audit of Agentic AI Frameworks", "0.90–1.00",
         "attack success rate, multi-agent systems, even in secured configs",
         "5 adversarial scenarios across LangChain, CrewAI, and multi-agent setups: prompt injection, tool injection, unauthorized execution, memory poisoning.",
         "#c9a84c"),
        ("FILE R2", "FAST Federated Unlearning", "95.02% → 0.0981",
         "backdoor attack success rate, zero false positives",
         "Extended the IEEE TNSE 2024 FAST framework across 3 attack types on 10 distributed clients, without full model retraining. 99% accuracy recovery.",
         "#a78bfa"),
        ("FILE R3", "Multi-Turn AI Safety Benchmark", "2.5×",
         "more frequent context-accumulation attack success",
         "Local eval across Llama3-8B, Hermes3-8B, Qwen2.5-7B via JailbreakBench and TruthfulQA. Introduced CARI, an original context-accumulation risk metric.",
         "#c9a84c"),
        ("FILE R4", "Seed-Free Data-to-Text Synthesis", "114.2%",
         "of fully-supervised baseline, zero-shot",
         "Zero-shot pipeline via Llama 3.1:8B across WebNLG, E2E, and WikiTableQuestions. Eliminates $5K–$50K of human annotation cost per dataset.",
         "#a78bfa"),
        ("FILE R5", "CIFAR-100 CNN Architecture", "68.01% → 93.34%",
         "reproduced baseline vs. enhanced result",
         "Reproduced Yang et al. (2023), then enhanced with residual attention and SE blocks for a +25.33% accuracy gain over the original baseline.",
         "#c9a84c"),
    ]
    cw, ch = 376, 270
    positions = [(24, 20), (412, 20), (800, 20), (24, 300), (412, 300)]
    pad = 20

    out = [svg_open(w, h)]
    for (x, y), (fileno, title, stat, statdesc, desc, color) in zip(positions, items):
        out.append(f'  <rect class="card" x="{x}" y="{y}" width="{cw}" height="{ch}" rx="2"/>')
        out.append(f'  <circle class="dot" cx="{x+22}" cy="{y+26}" r="3.5" fill="{color}"/>')
        out.append(f'  <text class="idx" x="{x+34}" y="{y+30}" style="font-size:12px">{fileno}</text>')

        ty = y + 58
        for tl in wrap_words(title, cw - pad * 2, 16.5, "syne"):
            out.append(f'  <text class="title" x="{x+pad}" y="{ty}" style="font-size:16.5px">{esc(tl)}</text>')
            ty += 21

        ty += 20
        out.append(f'  <text class="stat" x="{x+pad}" y="{ty}" style="font-size:24px" fill="{color}">{esc(stat)}</text>')
        ty += 20
        for sl in wrap_words(statdesc, cw - pad * 2, 10.5, "jbm"):
            out.append(f'  <text class="body" x="{x+pad}" y="{ty}" style="font-size:10.5px">{esc(sl)}</text>')
            ty += 14

        ty += 12
        for dl in wrap_words(desc, cw - pad * 2, 10.5, "jbm"):
            if ty > y + ch - 10:
                raise ValueError(f"research card overflow: '{title}'")
            out.append(f'  <text class="body" x="{x+pad}" y="{ty}" style="font-size:10.5px;opacity:0.8">{esc(dl)}</text>')
            ty += 15
    out.append("</svg>\n")
    open("research.svg", "w", encoding="utf-8").write("\n".join(out))
    print("wrote research.svg")


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


build_dossier()
build_skills()
build_projects_all()
build_research()
build_header("05", "SIGNAL TRACE", "header-05.svg")
build_header("06", "SECURE CHANNEL", "header-06.svg")
