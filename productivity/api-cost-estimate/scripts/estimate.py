#!/usr/bin/env python3
"""Estimate what local Claude Code usage would have cost on pay-as-you-go API pricing.

Reads every assistant turn in ~/.claude/projects/**/*.jsonl, dedupes by
(message id, requestId), aggregates tokens per model for the window, and prints
two box-drawn tables: token usage and estimated cost.

Usage:
  estimate.py                     # last 7 days (UTC) -> now
  estimate.py START               # START (YYYY-MM-DD, 00:00 UTC) -> now
  estimate.py START END           # START 00:00 UTC -> END 23:59:59 UTC
  estimate.py --prices prices.json ...   # override the pricing table

Pricing: first-party Claude API rates, USD per 1M tokens. Cache write is
billed at 1.25x input (5-minute TTL); cache read at 0.1x input. The 1-hour
cache TTL bills writes at 2x input; the upper bound printed below assumes
every write used it.
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import sys

UTC = dt.timezone.utc

# (display name, input $/1M, output $/1M). Key matches the `model` field prefix
# in transcripts. Update when Anthropic publishes new rates.
DEFAULT_PRICES = {
    "claude-fable-5": ("Fable 5", 10.0, 50.0),
    "claude-mythos-5": ("Mythos 5", 10.0, 50.0),
    "claude-opus-5": ("Opus 5", 5.0, 25.0),
    "claude-opus-4-8": ("Opus 4.8", 5.0, 25.0),
    "claude-opus-4-7": ("Opus 4.7", 5.0, 25.0),
    "claude-opus-4-6": ("Opus 4.6", 5.0, 25.0),
    "claude-sonnet-5": ("Sonnet 5", 2.0, 10.0),
    "claude-sonnet-4-6": ("Sonnet 4.6", 3.0, 15.0),
    "claude-haiku-4-5": ("Haiku 4.5", 1.0, 5.0),
}
CACHE_WRITE_5M = 1.25
CACHE_WRITE_1H = 2.0
CACHE_READ = 0.1


def parse_date(s, end=False):
    d = dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=UTC)
    return d + dt.timedelta(days=1) - dt.timedelta(seconds=1) if end else d


def lookup(model, prices):
    for key, val in prices.items():
        if model.startswith(key):
            return val
    return None


def aggregate(root, start, end):
    agg = collections.defaultdict(lambda: [0, 0, 0, 0, 0])  # in, out, cw, cr, reqs
    seen = set()
    for path in glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True):
        if os.path.getmtime(path) < start.timestamp():
            continue
        with open(path, errors="ignore") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if d.get("type") != "assistant":
                    continue
                m = d.get("message") or {}
                u = m.get("usage")
                if not u:
                    continue
                try:
                    t = dt.datetime.fromisoformat(d.get("timestamp", "").replace("Z", "+00:00"))
                except ValueError:
                    continue
                if not (start <= t <= end):
                    continue
                key = (m.get("id"), d.get("requestId"))
                if key in seen:
                    continue
                seen.add(key)
                a = agg[m.get("model", "?")]
                a[0] += u.get("input_tokens", 0)
                a[1] += u.get("output_tokens", 0)
                a[2] += u.get("cache_creation_input_tokens", 0)
                a[3] += u.get("cache_read_input_tokens", 0)
                a[4] += 1
    return agg


def fmt_tokens(n):
    if n == 0:
        return "~0"
    if n >= 1e6:
        return f"{n / 1e6:.2f}M" if n < 10e6 else f"{n / 1e6:.1f}M"
    if n >= 1e3:
        return f"{n / 1e3:.1f}K"
    return f"{n:,}"


def box(headers, rows, align_first_center=True):
    widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(len(headers))]
    def line(l, m, r):
        return l + m.join("─" * (w + 2) for w in widths) + r
    def cells(row, center=False):
        out = []
        for i, c in enumerate(row):
            c = str(c)
            out.append(" " + (c.center(widths[i]) if center else c.ljust(widths[i])) + " ")
        return "│" + "│".join(out) + "│"
    lines = [line("┌", "┬", "┐"), cells(headers, center=True), line("├", "┼", "┤")]
    for i, r in enumerate(rows):
        lines.append(cells(r))
        lines.append(line("├", "┼", "┤") if i < len(rows) - 1 else line("└", "┴", "┘"))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("start", nargs="?", help="YYYY-MM-DD (UTC). Default: 7 days ago")
    ap.add_argument("end", nargs="?", help="YYYY-MM-DD (UTC, inclusive). Default: now")
    ap.add_argument("--root", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--prices", help="JSON file: {model_prefix: [name, input_per_M, output_per_M]}")
    args = ap.parse_args()

    now = dt.datetime.now(UTC)
    start = parse_date(args.start) if args.start else (now - dt.timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = parse_date(args.end, end=True) if args.end else now
    prices = DEFAULT_PRICES
    if args.prices:
        with open(args.prices) as fh:
            prices = {k: tuple(v) for k, v in json.load(fh).items()}

    agg = aggregate(args.root, start, end)
    priced = [(k, v, lookup(k, prices)) for k, v in agg.items()]
    unknown = [k for k, v, p in priced if p is None and k != "<synthetic>"]
    priced = [(k, v, p) for k, v, p in priced if p]

    label_end = "now" if not args.end else end.strftime("%a %d %b")
    window = f"{start.strftime('%a %d %b')} → {label_end}"

    entries = []  # (total_5m, usage_row, cost_row)
    total_5m = total_1h = 0.0
    for k, v, (name, pin, pout) in priced:
        c_in = v[0] * pin / 1e6
        c_out = v[1] * pout / 1e6
        c_cw = v[2] * pin * CACHE_WRITE_5M / 1e6
        c_cr = v[3] * pin * CACHE_READ / 1e6
        tot = c_in + c_out + c_cw + c_cr
        total_5m += tot
        total_1h += tot - c_cw + v[2] * pin * CACHE_WRITE_1H / 1e6
        entries.append((
            tot,
            [name, f"{v[4]:,}", fmt_tokens(v[0]), fmt_tokens(v[1]), fmt_tokens(v[2]), fmt_tokens(v[3])],
            [f"{name} (${pin:g} / ${pout:g})", f"${c_in:.2f}", f"${c_out:.2f}", f"${c_cw:.2f}", f"${c_cr:.2f}", f"${tot:.2f}"],
        ))
    entries.sort(key=lambda e: -e[0])  # most expensive model first, same order in both tables
    usage_rows = [e[1] for e in entries]
    cost_rows = [e[2] for e in entries] + [["All models", "", "", "", "", f"≈ ${total_5m:,.0f}"]]

    print(f"Token usage ({window})\n")
    print(box(["Model", "Requests", "Input", "Output", "Cache write", "Cache read"], usage_rows))
    print(f"\nEstimated API cost (5-minute cache pricing)\n")
    print(box(["Model", "Input", "Output", "Cache write", "Cache read", "Total"], cost_rows))
    print(f"\n1-hour cache TTL upper bound: ≈ ${total_1h:,.0f}")
    if unknown:
        print(f"Unpriced models skipped: {', '.join(unknown)}", file=sys.stderr)


if __name__ == "__main__":
    main()
