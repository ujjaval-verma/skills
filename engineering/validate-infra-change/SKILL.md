---
name: validate-infra-change
description: Validate Kubernetes/IaC PR changes safely in a live non-production environment before merge. Use when asked to test, smoke, kubectl-apply, patch, canary, or validate infra manifests/overlays/Helm/Kustomize changes against dev/staging while preserving GitOps/Argo CD ownership and collecting log evidence. Covers targeted resource applies, Argo self-heal handling, rollback, runtime log checks, and final PR evidence.
updated: 2026-10-04
---

# Validate Infra Change

Live-smoke a PR's Kubernetes/IaC change in a non-production cluster without leaving drift or breaking GitOps ownership.

## Rails

- Before acting against any context that is not dev, stop and confirm the target with the operator.
- Apply only the objects the PR touches, never the whole overlay. A direct apply is temporary drift.
- Never print secrets; use in-pod assertions that output only pass/fail.
- Snapshot live YAML before any change: every object you may patch, every consumer you may restart, and the Argo `Application` itself. Keep snapshots in a timestamped temp dir.
- If Argo self-heal would revert the smoke patch, suspend only `selfHeal`/`prune`. Never change the source revision or broader project settings.

## Evidence

Prove it from runtime state: rollout status, pod and controller logs, secret-safe `kubectl exec` checks.

## Restore

Before finishing:

1. Re-apply the snapshots or sync back to the tracked revision, and restart consumers as needed.
2. Restore the exact prior sync policy captured in the snapshot.
3. Confirm the `Application` is Synced/Healthy at its tracked revision.
4. Confirm no residual drift: scale changes, annotations, test-only pods.

Report any drift you intentionally leave in place.
