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
      .titlew { font-family: 'SyneB','Trebuchet MS',sans-serif; font-weight: 800; fill: #e8eaf2; }
      .body { font-family: 'JBM',monospace; font-weight: 500; fill: #a0aac4; }
      .label { font-family: 'JBM',monospace; font-weight: 500; fill: #e8eaf2; }
      .idx { font-family: 'JBM',monospace; font-weight: 500; fill: #6b7a99; letter-spacing: 2px; }
      .tag { font-family: 'JBM',monospace; font-weight: 500; fill: #a78bfa; letter-spacing: 0.5px; }
      .pct { font-family: 'JBM',monospace; font-weight: 500; fill: #c9a84c; }
      .stat { font-family: 'SyneB','Trebuchet MS',sans-serif; font-weight: 800; }
      .chip { fill: none; stroke: #2a3050; stroke-width: 1; }
      .chiptxt { font-family: 'JBM',monospace; font-weight: 500; fill: #c9a84c; letter-spacing: 1px; }
      .dot { animation: pulse 2.2s ease-in-out infinite; transform-origin: center; }
      @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
      .barfill { animation: grow 1.4s ease-out both; }
      @keyframes grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
"""


def svg_open(w, h, extra_css=""):
    return f"""<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
{FONTS_CSS}
{BASE_CSS}
{extra_css}
    </style>
  </defs>
  <rect class="bg" width="{w}" height="{h}"/>
"""


def esc(s):
    return html.escape(s, quote=False)


# ---------------------------------------------------------------- dossier.svg
def build_dossier():
    w, h = 1200, 360
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

    chips = [
        ("B.S. ARTIFICIAL INTELLIGENCE — FAST-NUCES", "#c9a84c"),
        ("CGPA 3.62 / 4.0 — DEAN'S LIST ×5 · RECTOR'S LIST", "#a78bfa"),
        ("TEACHING ASSISTANT — AGENTIC AI", "#c9a84c"),
        ("AVAILABLE JUN 2026", "#a78bfa"),
    ]
    cx, cy = 24, y + 20
    for text, color in chips:
        cw = 18 + len(text) * 7.3
        out.append(f'  <rect class="chip" x="{cx}" y="{cy}" width="{cw:.0f}" height="26" rx="2"/>')
        out.append(f'  <circle class="dot" cx="{cx+14}" cy="{cy+13}" r="3" fill="{color}"/>')
        out.append(f'  <text class="chiptxt" x="{cx+26}" y="{cy+17}" style="font-size:11.5px">{esc(text)}</text>')
        cx += cw + 14
        if cx > 1000:
            cx = 24
            cy += 38

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


# --------------------------------------------------------- projects-ops.svg
def build_projects_ops():
    w, h = 1200, 300
    cards = [
        ("FILE 08", "DETECTIFAI", "Real-time CCTV threat detection — weapons, intrusions,\nbehavioral anomalies. YOLO + CLIP vision-language +\nFaceNet identity tracking.", "YOLO · CLIP · FASTAPI", "#c9a84c", None),
        ("FILE 09", "MULTI-TENANT\nAGENTIC RAG", "Tenant isolation, ACL enforcement, PII masking, prompt-\ninjection detection. Passed red-team evaluation.", "LANGCHAIN · CREWAI", "#a78bfa", "https://github.com/blacksinisterx/Multi-Tenant-Agentic-RAG-System"),
        ("FILE 10", "CRISSIM —\nDISASTER RESPONSE", "Heterogeneous agents simulating earthquake response,\nmedic + drone coordination. Benchmarks ReAct,\nReflexion, and Chain-of-Thought against each other.", "LANGGRAPH · REACT", "#c9a84c", "https://github.com/blacksinisterx/CrisSim-Multi-Agent-Simulation"),
        ("FILE 11", "AGENTIC AIRSPACE\nCOPILOT", "Live flight-anomaly detection on real OpenSky API data.\nCrewAI + LangGraph orchestration with MCP tool\nintegration.", "CREWAI · MCP", "#a78bfa", "https://github.com/sincera315/Assignment3_Agentic_AI_N8N"),
    ]
    out = [svg_open(w, h)]
    cw = 273
    for i, (fileno, title, desc, tags, color, link) in enumerate(cards):
        x = 24 + i * (cw + 12)
        out.append(f'  <rect class="card" x="{x}" y="20" width="{cw}" height="260" rx="2"/>')
        out.append(f'  <circle class="dot" cx="{x+22}" cy="46" r="3.5" fill="{color}" style="animation-delay:-{i*0.4}s"/>')
        out.append(f'  <text class="idx" x="{x+34}" y="50" style="font-size:12px">{fileno}</text>')
        ty = 80
        for tline in title.split("\n"):
            out.append(f'  <text class="title" x="{x+20}" y="{ty}" style="font-size:19px">{esc(tline)}</text>')
            ty += 24
        dy = ty + 20
        for dline in desc.split("\n"):
            out.append(f'  <text class="body" x="{x+20}" y="{dy}" style="font-size:11.5px">{esc(dline)}</text>')
            dy += 17
        out.append(f'  <text class="tag" x="{x+20}" y="{20+260-16}" style="font-size:10px">{esc(tags)}</text>')
    out.append("</svg>\n")
    open("projects-ops.svg", "w", encoding="utf-8").write("\n".join(out))
    print("wrote projects-ops.svg")


# -------------------------------------------------------------- research.svg
def build_research():
    w, h = 1200, 560
    items = [
        ("FILE R1", "SECURITY AUDIT OF\nAGENTIC AI FRAMEWORKS", "0.90–1.00", "attack success rate — multi-agent\nsystems, even secured", "5 adversarial scenarios across LangChain, CrewAI, and\nmulti-agent setups: prompt injection, tool injection,\nunauthorized execution, memory poisoning.", "#c9a84c"),
        ("FILE R2", "FAST FEDERATED\nUNLEARNING", "95.02% → 0.0981", "backdoor attack success rate,\nzero false positives", "Extended the IEEE TNSE 2024 FAST framework across 3\nattack types on 10 distributed clients, without full\nmodel retraining. 99% accuracy recovery.", "#a78bfa"),
        ("FILE R3", "MULTI-TURN AI SAFETY\nBENCHMARK", "2.5×", "more frequent context-\naccumulation attack success", "Local eval across Llama3-8B, Hermes3-8B, Qwen2.5-7B\nvia JailbreakBench + TruthfulQA. Introduced CARI, an\noriginal context-accumulation risk metric.", "#c9a84c"),
        ("FILE R4", "SEED-FREE DATA-TO-\nTEXT SYNTHESIS", "114.2%", "of fully-supervised baseline,\nzero-shot", "Zero-shot pipeline via Llama 3.1:8B across WebNLG,\nE2E, WikiTableQuestions. Eliminates $5K–$50K of\nhuman annotation cost per dataset.", "#a78bfa"),
        ("FILE R5", "CIFAR-100 CNN\nARCHITECTURE", "68.01% → 93.34%", "reproduced baseline vs.\nenhanced result", "Reproduced Yang et al. (2023), then enhanced with\nresidual attention + SE blocks for a +25.33% accuracy\ngain over the original baseline.", "#c9a84c"),
    ]
    out = [svg_open(w, h)]
    cw, ch = 376, 260
    positions = [(24, 20), (412, 20), (800, 20), (24, 296), (412, 296)]
    for (x, y), (fileno, title, stat, statdesc, desc, color) in zip(positions, items):
        out.append(f'  <rect class="card" x="{x}" y="{y}" width="{cw}" height="{ch}" rx="2"/>')
        out.append(f'  <circle class="dot" cx="{x+22}" cy="{y+26}" r="3.5" fill="{color}"/>')
        out.append(f'  <text class="idx" x="{x+34}" y="{y+30}" style="font-size:12px">{fileno}</text>')
        ty = y + 58
        for tline in title.split("\n"):
            out.append(f'  <text class="title" x="{x+20}" y="{ty}" style="font-size:16.5px">{esc(tline)}</text>')
            ty += 21
        out.append(f'  <text class="stat" x="{x+20}" y="{ty+30}" style="font-size:25px" fill="{color}">{esc(stat)}</text>')
        sdy = ty + 50
        for sline in statdesc.split("\n"):
            out.append(f'  <text class="body" x="{x+20}" y="{sdy}" style="font-size:10.5px">{esc(sline)}</text>')
            sdy += 14
        ddy = sdy + 14
        for dline in desc.split("\n"):
            out.append(f'  <text class="body" x="{x+20}" y="{ddy}" style="font-size:10.5px;opacity:0.8">{esc(dline)}</text>')
            ddy += 15
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
    out = [svg_open(1200, 76, extra)]
    out.append("""
  <defs>
    <linearGradient id="pulseGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#c9a84c" stop-opacity="0"/>
      <stop offset="50%" stop-color="#e8d08a" stop-opacity="1"/>
      <stop offset="100%" stop-color="#a78bfa" stop-opacity="0"/>
    </linearGradient>
  </defs>
""")
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
build_projects_ops()
build_research()
build_header("05", "SIGNAL TRACE", "header-05.svg")
build_header("06", "SECURE CHANNEL", "header-06.svg")
