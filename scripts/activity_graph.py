#!/usr/bin/env python3
"""Draws the last 12 months of GitHub contributions as two self-hosted SVGs (dark and light).

Replaces github-readme-activity-graph.vercel.app, which is gone (HTTP 402 DEPLOYMENT_DISABLED).
Data comes from GitHub's own GraphQL API, so nothing depends on a third-party host.

  GITHUB_TOKEN=... GH_USER=blacksinisterx python scripts/activity_graph.py          # writes dist/activity-{dark,light}.svg
  python scripts/activity_graph.py --json sample.json --out /tmp/x                  # offline, for testing
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.request
from html import escape

QUERY = ('{ user(login: "%s") { contributionsCollection { contributionCalendar { totalContributions '
         'weeks { firstDay contributionDays { contributionCount } } } } } }')

THEMES = {  # same palette as the rest of the profile README
    'dark': dict(bg='#07080f', text='#a0aac4', title='#e8eaf2', line='#c9a84c', point='#a78bfa', area='#3d2d7a', grid='#1e2235'),
    'light': dict(bg='#f6f2e4', text='#4a4636', title='#1c1810', line='#6d46b8', point='#a8873a', area='#f2e0a8', grid='#ddd3b0'),
}


def fetch(user, token):
    req = urllib.request.Request(
        'https://api.github.com/graphql', data=json.dumps({'query': QUERY % user}).encode(),
        headers={'Authorization': f'bearer {token}', 'User-Agent': 'profile-activity-graph', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get('errors') or not body.get('data', {}).get('user'):
        sys.exit(f'GitHub GraphQL error: {body.get("errors") or "no such user"}')
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


def render(weeks, total, t):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', help='read a saved GraphQL response instead of calling the API')
    ap.add_argument('--out', default='dist')
    a = ap.parse_args()
    if a.json:
        data = json.load(open(a.json, encoding='utf8'))
        data = data.get('data', data)
    else:
        token, user = os.environ.get('GITHUB_TOKEN'), os.environ.get('GH_USER')
        if not token or not user:
            sys.exit('set GITHUB_TOKEN and GH_USER')
        data = fetch(user, token)
    weeks, total = weekly(data)
    if len(weeks) < 2:
        sys.exit('not enough weeks of data to draw a graph')
    os.makedirs(a.out, exist_ok=True)
    for name, theme in THEMES.items():
        with open(os.path.join(a.out, f'activity-{name}.svg'), 'w', encoding='utf8') as f:
            f.write(render(weeks, total, theme))
    print(f'wrote activity-dark.svg and activity-light.svg: {len(weeks)} weeks, {total} contributions')


if __name__ == '__main__':
    main()
