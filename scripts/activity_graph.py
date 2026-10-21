#!/usr/bin/env python3
"""Draws the profile's live stats as self-hosted SVGs (dark and light): the 12-month activity graph and the streak card.

Replaces github-readme-activity-graph.vercel.app (gone, HTTP 402) and streak-stats.demolab.com (cached for a day).
Everything comes from GitHub's own GraphQL API, so nothing depends on a third-party host.

  GITHUB_TOKEN=... GH_USER=blacksinisterx python scripts/activity_graph.py   # writes dist/{activity,streak}-{dark,light}.svg
  python scripts/activity_graph.py --json sample.json --out /tmp/x           # offline graph from a saved response
  python scripts/activity_graph.py --selftest                                # checks the streak arithmetic
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.request
from html import escape


def fail(msg):
    # in GitHub Actions an ::error:: line becomes a run annotation, readable without logging in
    if os.environ.get('GITHUB_ACTIONS'):
        print(f'::error::{msg}')
    else:
        print(msg, file=sys.stderr)
    sys.exit(1)


QUERY = ('{ user(login: "%s") { contributionsCollection { contributionYears contributionCalendar { totalContributions '
         'weeks { firstDay contributionDays { contributionCount } } } } } }')
DAYS = 'y%d: contributionsCollection(from: "%d-01-01T00:00:00Z", to: "%s") { contributionCalendar { weeks { contributionDays { date contributionCount } } } }'

THEMES = {  # same palette as the rest of the profile README
    'dark': dict(bg='#07080f', text='#a0aac4', title='#e8eaf2', line='#c9a84c', point='#a78bfa', area='#3d2d7a', grid='#1e2235',
                 ring='#c9a84c', fire='#e8d08a', num='#e8eaf2', dates='#6b7a99', stroke='#1e2235'),
    'light': dict(bg='#f6f2e4', text='#4a4636', title='#1c1810', line='#6d46b8', point='#a8873a', area='#f2e0a8', grid='#ddd3b0',
                  ring='#6d46b8', fire='#9b7ee0', num='#1c1810', dates='#8a7f5e', stroke='#ddd3b0'),
}


def gql(query, token):
    req = urllib.request.Request(
        'https://api.github.com/graphql', data=json.dumps({'query': query}).encode(),
        headers={'Authorization': f'bearer {token}', 'User-Agent': 'profile-activity-graph', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.load(r)
    except Exception as e:  # HTTPError carries the status and GitHub's message
        detail = ' '.join(e.read().decode('utf8', 'replace')[:300].split()) if hasattr(e, 'read') else ''
        fail(f'GraphQL request failed: {e} {detail}')
    if body.get('errors') or not body.get('data'):
        fail(f'GitHub GraphQL error: {body.get("errors") or "no data"}')
    return body['data']


def weekly(data):
    cal = data['user']['contributionsCollection']['contributionCalendar']
    weeks = [(w['firstDay'], sum(d['contributionCount'] for d in w['contributionDays'])) for w in cal['weeks']]
    return weeks, cal['totalContributions']


def nice_max(v):
    for step in (5, 10, 20, 25, 50, 100, 200, 500, 1000):
        if v <= step * 4:
            return step * 4, step
    return int(v) + 1, max(1, int(v) // 4)


def render_activity(weeks, total, t):
    W, H, L, R, T, B = 880, 230, 46, 22, 58, 34
    top, step = nice_max(max(v for _, v in weeks) or 1)
    n = len(weeks)
    x = lambda i: L + i * (W - L - R) / max(1, n - 1)
    y = lambda v: H - B - v / top * (H - T - B)
    pts = [(x(i), y(v)) for i, (_, v) in enumerate(weeks)]
    line = 'M' + ' L'.join(f'{px:.1f},{py:.1f}' for px, py in pts)
    area = f'{line} L{pts[-1][0]:.1f},{H - B} L{pts[0][0]:.1f},{H - B} Z'
    grid = ''.join(
        f'<line x1="{L}" x2="{W - R}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="{t["grid"]}" stroke-width="1"/>'
        f'<text x="{L - 8}" y="{y(g) + 4:.1f}" text-anchor="end" fill="{t["text"]}" font-size="11">{g}</text>'
        for g in range(0, top + 1, step))
    months, seen = '', None
    for i, (day, _) in enumerate(weeks):
        d = dt.date.fromisoformat(day)
        if d.month != seen and d.day <= 7:
            months += f'<text x="{x(i):.1f}" y="{H - 12}" text-anchor="middle" fill="{t["text"]}" font-size="11">{d.strftime("%b")}</text>'
            seen = d.month
    dots = ''.join(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.6" fill="{t["point"]}"/>' for (px, py), (_, v) in zip(pts, weeks) if v)
    label = f'Contribution activity, last 12 months: {total} contributions, weekly totals'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}" '
            f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"><title>{escape(label)}</title>'
            f'<rect width="{W}" height="{H}" rx="8" fill="{t["bg"]}"/>'
            f'<text x="{L}" y="30" fill="{t["title"]}" font-size="14" font-weight="700" letter-spacing="2">CONTRIBUTION TELEMETRY</text>'
            f'<text x="{W - R}" y="30" text-anchor="end" fill="{t["text"]}" font-size="12">{total} in the last 12 months</text>'
            f'{grid}<path d="{area}" fill="{t["area"]}" opacity="0.55"/>'
            f'<path d="{line}" fill="none" stroke="{t["line"]}" stroke-width="2" stroke-linejoin="round"/>{dots}{months}</svg>\n')


# ---------- streak card ----------

def fetch_days(years, token, now):
    parts = []
    for yr in years:
        end = now.strftime('%Y-%m-%dT%H:%M:%SZ') if yr == now.year else f'{yr}-12-31T23:59:59Z'
        parts.append(DAYS % (yr, yr, end))
    data = gql('{ user(login: "%s") { %s } }' % (os.environ['GH_USER'], ' '.join(parts)), token)['user']
    days = {}
    for key in data.values():
        for w in key['contributionCalendar']['weeks']:
            for d in w['contributionDays']:
                days[dt.date.fromisoformat(d['date'])] = d['contributionCount']
    return days


def streak_stats(days, today):
    """A streak is consecutive days with at least one contribution. A day that has not ended yet does not break it."""
    first = min((d for d, c in days.items() if c > 0), default=None)
    if first is None:
        return None
    runs, start, prev, d = [], None, None, first
    while d <= today:
        if days.get(d, 0) > 0:
            start, prev = start or d, d
        elif start and d != today:
            runs.append((start, prev))
            start = None
        d += dt.timedelta(days=1)
    if start:
        runs.append((start, prev))
    longest = max(runs, key=lambda r: ((r[1] - r[0]).days, r[1]))
    cur = runs[-1] if runs[-1][1] >= today - dt.timedelta(days=1) else None
    return dict(total=sum(c for d, c in days.items() if d >= first), first=first, cur=cur, longest=longest)


def selftest():
    D = dt.date
    days = {D(2026, 1, 1): 2, D(2026, 1, 2): 1, D(2026, 1, 3): 4, D(2026, 1, 5): 1}
    s = streak_stats(days, D(2026, 1, 6))  # today (Jan 6) is still empty: Jan 5 keeps a 1-day streak alive
    assert s['total'] == 8 and s['longest'] == (D(2026, 1, 1), D(2026, 1, 3)) and s['cur'] == (D(2026, 1, 5), D(2026, 1, 5)), s
    s = streak_stats(days, D(2026, 1, 7))  # Jan 6 and Jan 7 empty: no current streak
    assert s['cur'] is None and s['longest'] == (D(2026, 1, 1), D(2026, 1, 3)), s
    days[D(2026, 1, 6)] = 1
    s = streak_stats(days, D(2026, 1, 6))
    assert s['cur'] == (D(2026, 1, 5), D(2026, 1, 6)), s
    print('selftest ok')


def label(a, b, today):
    f = lambda d: f"{d.strftime('%b')} {d.day}" + ('' if d.year == today.year else f', {d.year}')
    return f(a) if a == b else f'{f(a)} - {f(b)}'


def render_streak(st, today, t):
    W, H = 495, 195
    first = st['first']
    cur = st['cur']
    cur_n = (cur[1] - cur[0]).days + 1 if cur else 0
    lo = st['longest']
    lo_n = (lo[1] - lo[0]).days + 1
    txt = lambda x, y, s, size, fill, weight='400': (
        f'<text x="{x}" y="{y}" text-anchor="middle" fill="{fill}" font-size="{size}" font-weight="{weight}">{escape(str(s))}</text>')
    summary = f'{st["total"]} total contributions, current streak {cur_n} days, longest streak {lo_n} days'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(summary)}" '
            f'font-family="\'Segoe UI\', Ubuntu, \'Helvetica Neue\', Arial, sans-serif"><title>{escape(summary)}</title>'
            f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="4.5" fill="{t["bg"]}" stroke="{t["stroke"]}"/>'
            f'<line x1="165" x2="165" y1="28" y2="167" stroke="{t["stroke"]}"/><line x1="330" x2="330" y1="28" y2="167" stroke="{t["stroke"]}"/>'
            + txt(82.5, 82, st['total'], 28, t['num'], '700') + txt(82.5, 112, 'Total Contributions', 14, t['text'])
            + txt(82.5, 145, f'{first.strftime("%b")} {first.day}, {first.year} - Present', 12, t['dates'])
            + f'<circle cx="247.5" cy="72" r="40" fill="none" stroke="{t["ring"]}" stroke-width="5"/>'
              f'<circle cx="247.5" cy="32" r="12" fill="{t["bg"]}"/>'
              f'<path transform="translate(247.5 31)" fill="{t["fire"]}" d="M0,-12 C2,-7 9,-4 9,3 C9,8 5,11 0,11 C-5,11 -9,8 -9,3 C-9,0 -7,-2 -5,-4 C-5,-1 -3,1 -1,0 C-2,-4 -2,-8 0,-12 Z"/>'
            + txt(247.5, 82, cur_n, 28, t['num'], '700') + txt(247.5, 140, 'Current Streak', 14, t['title'], '700')
            + txt(247.5, 165, label(cur[0], cur[1], today) if cur else 'No active streak', 12, t['dates'])
            + txt(412.5, 82, lo_n, 28, t['num'], '700') + txt(412.5, 112, 'Longest Streak', 14, t['text'])
            + txt(412.5, 145, label(lo[0], lo[1], today), 12, t['dates']) + '</svg>\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', help='read a saved GraphQL response instead of calling the API (graph only)')
    ap.add_argument('--out', default='dist')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    token = os.environ.get('GITHUB_TOKEN')
    if a.json:
        data = json.load(open(a.json, encoding='utf8'))
        data = data.get('data', data)
    else:
        if not token or not os.environ.get('GH_USER'):
            fail('set GITHUB_TOKEN and GH_USER')
        data = gql(QUERY % os.environ['GH_USER'], token)
    weeks, total = weekly(data)
    if len(weeks) < 2:
        fail('not enough weeks of data to draw a graph')
    os.makedirs(a.out, exist_ok=True)
    write = lambda name, theme, svg: open(os.path.join(a.out, f'{name}-{theme}.svg'), 'w', encoding='utf8').write(svg)
    for theme, t in THEMES.items():
        write('activity', theme, render_activity(weeks, total, t))
    made = f'activity graph: {len(weeks)} weeks, {total} contributions'
    years = data['user']['contributionsCollection'].get('contributionYears')
    if years and not a.json:
        now = dt.datetime.now(dt.timezone.utc)
        st = streak_stats(fetch_days(years, token, now), now.date())
        if st:
            for theme, t in THEMES.items():
                write('streak', theme, render_streak(st, now.date(), t))
            made += f'; streak card: {st["total"]} total, current {st["cur"]}, longest {st["longest"]}'
    print('wrote ' + made)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # unexpected: still show the cause in the annotation
        fail(f'{type(e).__name__}: {e}')
