---
name: network-connectivity-troubleshoot
description: Diagnose and work around public-network, DNS, GitHub gh, Linear, web_search/web_fetch, package install, OAuth/API, or model-provider connectivity failures, especially when Tailscale/tailnet routing may be interfering. Use before assuming auth/model/provider failure when public internet calls fail while Tailscale is connected. Provides a Tailscale escape hatch: disconnect and stay disconnected unless tailnet access is needed.
updated: 2026-07-07
---

# Network Connectivity Troubleshoot

Use this when public-network calls fail or time out: `gh`, Linear, web search/fetch, package installs, OAuth/API/provider calls, model routing/fallback oddities, or DNS failures.

## First checks

1. Identify whether the failing command needs the public internet or the tailnet.
2. If it needs the tailnet (`kubectl` to `*.ts.net`, tailnet SSH, private service), keep Tailscale up and diagnose tailnet separately.
3. If it needs public internet, suspect Tailscale routing/DNS before assuming auth, provider, or model failure.

## Escape hatch: public internet first

If public-network calls are failing while Tailscale is up and no tailnet-dependent command is active:

```bash
tailscale status >/dev/null 2>&1 && tailscale down
```

Then retry the public operation directly, e.g.:

```bash
gh api rate_limit
linear issue get TEAM-123
```

**Done when** the originally-failing command, re-run with Tailscale down, returns success. If it still fails, Tailscale routing was not the cause — move on to public-outage or auth/provider diagnosis (keys, OAuth, provider status, model fallback).

**Stay disconnected.** Reconnect only when a tailnet command is next, or the user asks.

## One-off safe wrapper when you must restore tailnet

Use this only when you know tailnet access is needed immediately after the public operation:

```bash
set -euo pipefail
was_up=0
if tailscale status >/dev/null 2>&1; then
  was_up=1
  tailscale down
fi
trap 'if [ "$was_up" = 1 ]; then tailscale up; fi' EXIT

# public-network command here
gh api rate_limit
```

## Reconnect when tailnet is required

Before a tailnet command, reconnect and verify with the smallest safe tailnet-dependent probe for the current environment:

```bash
tailscale up
tailscale status
# Example: ssh <tailnet-host> true, kubectl --context <tailnet-context> get ns, or curl https://<private-service>
```
