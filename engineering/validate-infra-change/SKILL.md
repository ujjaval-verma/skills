---
name: validate-infra-change
description: Validate Kubernetes/IaC PR changes safely in a live non-production environment before merge. Use when asked to test, smoke, kubectl-apply, patch, canary, or validate infra manifests/overlays/Helm/Kustomize changes against dev/staging while preserving GitOps/Argo CD ownership and collecting log evidence. Covers targeted resource applies, Argo self-heal handling, rollback, runtime log checks, and final PR evidence.
---

# Validate Infra Change

Use this skill to live-smoke Kubernetes/IaC changes from a PR in dev/staging without leaving permanent drift or breaking GitOps deployment flow.

## Principles

- Prefer **targeted applies** of only PR-touched resources over broad overlay applies.
- Treat direct `kubectl apply` as temporary drift. Snapshot first, validate, then hand control back to GitOps.
- Use real runtime evidence: rollout state, pod logs, generated config checks, service connectivity, and controller status.
- Never print secrets. Use grep/shape checks, redaction, or in-pod assertions that only output pass/fail.
- If a network/VPN/tailnet is required for the cluster but public Git/GitHub needs normal internet, switch deliberately and record which mode is active.

## Workflow

### 1. Preflight

1. Confirm the repo, branch, PR head, target environment, namespace, and cluster context.
2. Check local tree state; do not mix unrelated changes.
3. Inspect GitOps controller state when present, e.g. Argo CD Application sync/health/revision/syncPolicy.
4. Decide network mode:
   - cluster access may require VPN/tailnet;
   - public GitHub/Git operations may require VPN/tailnet down.

### 2. Render and snapshot

1. Render the PR manifests with the repo-native command, e.g. `kubectl kustomize`, `kustomize build`, or `helm template`.
2. Snapshot current live rollback YAML for every object that may be patched or restarted:
   - PR-touched ConfigMaps/Secrets/Deployments/Services/etc.;
   - dependent consumers that need restart to pick up ConfigMap/Secret changes;
   - GitOps Application/controller resource.
3. Store snapshots in a timestamped temp directory and mention it in the final evidence.

### 3. Filter resources

Create a manifest containing only the intended objects. Include namespace metadata if the render omits it. Avoid applying unrelated resources from the full overlay.

Typical examples:

- config object changed by the PR;
- deployment/statefulset/daemonset consuming that config;
- registration or service objects changed by the PR.

### 4. Validate before mutate

Run server-side dry-run on the filtered manifest:

```bash
kubectl --context "$CTX" -n "$NS" apply --dry-run=server -f filtered.yaml
```

Also run repo-local format/render checks where available.

### 5. Handle GitOps self-heal

If Argo CD or another GitOps controller has automated self-heal/prune enabled and would immediately revert the smoke patch:

1. Snapshot the controller resource first.
2. Temporarily suspend only the automated self-heal/prune portion needed for the test.
3. Do **not** change source revision or broad project settings unless explicitly required.
4. Restore the exact intended policy after rollback.

### 6. Apply and roll out

1. Apply the filtered manifest.
2. Restart only workloads that need it to consume config/registration changes.
3. Watch rollout status for changed and restarted workloads.
4. Capture pod and deployment state after rollout.

### 7. Functional smoke from logs

Collect actual logs and secret-safe runtime checks. Evidence should answer:

- Did init/config generation succeed?
- Did the process start and stay running?
- Did required dependencies connect successfully?
- Did structured logging/log routing behave as expected?
- Did generated runtime config preserve important placeholders and avoid secret leakage?
- Did dependent services/controllers stop emitting relevant warnings/errors?

Use `kubectl logs`, `kubectl exec` assertions, and controller logs. Save evidence to the run directory.

### 8. Patch the PR if smoke reveals drift

If live smoke finds a real issue:

1. Patch the PR branch.
2. Re-render and server-dry-run.
3. Re-apply only affected resources.
4. Re-run the functional smoke until clean.
5. Commit and push the fix when requested/appropriate.

### 9. Roll back and restore GitOps ownership

Before finishing:

1. Re-apply pre-smoke live resources or trigger GitOps sync back to its tracked revision.
2. Restart any consumers necessary to return to the tracked state.
3. Restore GitOps automated sync/self-heal/prune policy.
4. Force/refresh reconciliation if needed.
5. Verify GitOps reports healthy/synced at its tracked revision.
6. Verify no test-only pods, scale changes, annotations, or manual drift remain unless intentionally documented.

### 10. Final evidence

Report concisely:

- branch/PR head tested;
- resources patched;
- rollouts/restarts performed;
- concrete log evidence;
- any bugs found and commits made;
- rollback status and GitOps sync/health/revision;
- remaining blockers, especially approvals or intentional scale/ignore mitigations.
