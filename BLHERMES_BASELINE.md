# BLHermes baseline audit

Audit of the checkout initially at `661cd4900af6b1d658f4d7fec3390a220af3dd36`.
This is an evidence record, not a certification of every supported platform.
Future project integrations below are proposals only.

## Provenance

The initial working tree was clean on `main`, tracking `origin/main`.
Origin is `git@github.com:Justadudeinspace/blhermes-agent.git`.
The repository has full history (57,519 commits reachable from the initial HEAD).
An HTTPS fetch of NousResearch/hermes-agent main established:

| Identity | Commit |
| --- | --- |
| Shared upstream base | `3fa571a51a6bf1220dfe9a7a23fcd5bb9482a1af` |
| Observed upstream main | `55ee4acdd822b73fb9573a2321531ae3a9d0b3e0` |
| Initial fork HEAD | `661cd4900af6b1d658f4d7fec3390a220af3dd36` |

`git rev-list --left-right --count HEAD...FETCH_HEAD` returned `2 7` before
this audit's changes. The two fork commits (`67c8a453c7`, `661cd4900a`)
only change README branding: title and the BLUX Assimilated line. No runtime
delta existed at the start. The upstream reference is a dated observation,
not a claim that the remote cannot move. No upstream merge was performed.

## Cleanliness findings

`hermes_constants_scratch.py` and `hermes_constants_scratch_stuck.py` are
intentional facade siblings, not abandoned experiments. The former owns idle
scratch retention, process reaping, and worktree cleanup. The latter tracks
entries this user cannot remove and retries when permission fingerprints change.
Callers include `hermes_constants.py`, `tools/environments/local.py`,
`hermes_cli/doctor_state.py`, and the canonical test runner. History includes
`3cbe7b19db` and `78e298e94f`; behavioral coverage lives in
`tests/test_scratch_{dir,scan_failures,prune_undeletable}.py`. Retain both.

Tracked `plugins/{kanban,hermes-achievements}/dashboard/dist/` assets are
shipped dashboard products. `scripts/build/` is build implementation, not
stale build output. Generated icons are deliberately committed and checked
for freshness (CONTRIBUTING.md). None of these is sufficient evidence for
deletion. No source cleanup was justified by the initial inventory.

The targeted TODO/FIXME/HACK scan of PM, Termux, host detection, and Codex
runtime modules did not establish an unfinished-behavior defect. This does
not prove that every module or script is reachable: dynamic plugin discovery,
CLI entry points, workflow references, and skills preclude a simple import
grep as an orphan detector. No dead compatibility shim was removed.

Dependency authorities are root `pyproject.toml` / `uv.lock`, PM's separate
project and lock, `pm/lock.json`, root npm workspace manifest/lock, website's
independent npm manifest/lock, and the separately packaged bridge/sidecar
locks. Lockfile existence alone does not prove installed dependency currency.
No pins or lockfiles were changed as an incidental cleanup.

## Development environment and validation

Read root AGENTS.md, CONTRIBUTING.md, SECURITY.md, package-management developer
workflow, PM and test rules before changes. The supported path is isolated
`HERMES_HOME` and `HERMES_RUNTIME_DIR`, activation / PM, canonical
`scripts/run_tests.sh`, and `python scripts/check`. JS dependencies use root
`npm ci`; the website has its own install and `build:fast`.

This host is aarch64 Debian glibc 2.41 under PRoot on an Android kernel.
Initially `python` resolved to Termux Python 3.14.8 (`sys.platform == "android"`),
while Node was 20.19.2, below the root engine requirement. This is not a clean
native Linux host or an installed BLHermes Android APT runtime.

Disposable state and raw logs are in the host temporary directory's
`blhermes-baseline/` subdirectory; they are
not release artifacts and may disappear after reboot. No production credentials
were copied. Initial activation downloaded glibc CPython 3.14.7 but pinned uv
0.12.3's subsequent `python find --managed-python 3.14` rejected the discovered
interpreter with “only managed interpreters allowed.” Running that interpreter
directly succeeded and reported Linux/glibc. PM was then invoked through it
using the same operation as setup (`python -m pm.cli install --test-environment
--trust-recorded`). The resumed probe reproduced that failure with and without `--no-project`.
uv's verbose log finds the managed installation and then rejects it as unmanaged.
That interpreter's `sys.prefix` contains the host-side proot container root,
while its executable is found through the Debian guest path. This establishes a
path-identity mismatch on this host; a native supported Linux reproduction and
an upstream uv diagnosis are still required before changing bootstrap policy.
It is not a repair or proof of native Termux support. No raw pip/uv environment mutation
was used.

Validation receipts and remaining failures are recorded below after execution.

## Termux investigation

The warning was introduced by upstream commit
`4c89dbf880fb5e62bd2e2229088739cc4f28cbe0` on September 24, 2026. Its message
says the APT package does not work and a fix is in progress. Neither the
warning nor that commit supplies a crash trace or an exact technical cause.
Consequently the original reported failure's root cause remains **unproven**
from this evidence. Do not substitute a plausible native-dependency problem
for a reproduced failure.

The implementation has substantial Android-specific machinery:

| Layer | Existing implementation / limitation |
| --- | --- |
| Interpreter and tools | `scripts/termux/build_cpython.sh`, `build_node.sh`, `build_uv.sh`, and `termux_pkg_build.sh` stage pinned bionic artifacts from PM's `linux-arm64-bionic` rows. |
| Native graph | `termux_build.sh` and `build_wheels.py` export the locked graph, select Android markers, build native dependencies against bionic, and enforce offline completeness/import gates. |
| ABI/linker | `build_config.sh` declares `android_24_arm64_v8a` / `cp314`; `retag_wheel.py` rewrites wheel metadata; `python_linkage.py` adds the correct libpython SONAME when extensions have unresolved Python symbols. Retagging alone does not make a glibc wheel bionic-compatible. |
| Known dependency constraints | Android psutil uses a full-SHA source pin for upstream platform recognition; uvloop excludes Android. `termux-all` is distinct from desktop `all`; `BUILD_MISSES` records nemo-relay, whose supported-platform markers also exclude Android. |
| Runtime libraries | `stage_runtime_libs.py` stages the transitive runtime closure; `pm update --termux` repairs retired rolling-pool pins. A stale pool URL is a separate possible build failure, not proof of the warning's cause. |
| TUI and Node | `scripts/termux/build.py` builds the shared Ink product before `.deb` assembly. Node is bundled; installing an arbitrary Termux Node is not the release contract. |
| Resolution | `hermes_platform` owns OS/executable facts; PM has a bionic target. Inspect the actual interpreter's `sys.platform`, not only `uname`, when validating native paths. |
| Home and ownership | Standard Termux prefix and aarch64 only. Application payload under `$PREFIX/lib/hermes-agent`; profile-aware user state remains outside the package via `get_hermes_home()`. |
| Plugins/extras | Pure Python and declared Android-compatible dependencies can work; arbitrary native plugin dependencies are not guaranteed. Plugin admission and optional-dependency PM behavior still need device exercise. |
| Gateway | Foreground gateway is documented; Android may suspend or terminate background sessions. Wake locks are not durability guarantees. |
| Updates | Package owner is APT; tagged builds refuse source self-update and direct users to `pkg upgrade hermes-agent`. Commit artifacts deliberately refuse channel updates. |
| Release | `.github/workflows/termux-verify.yml` runs packaging contracts/TUI checks. Native runtime verification requires release-signing/R2 setup and can skip on unprovisioned forks; green fork CI alone proves no native runtime. The bundled-release workflow builds Termux only when selected and validates the assembled package. |

`scripts/termux/validate_installed.py` already exercises CLI version/help,
ACP check, stdlib/backend imports, every recorded native-wheel import,
Node/npm/rg, FFmpeg conversion, PM tool verification, updater refusal, and a
real TUI setup screen under a PTY. Reuse this before adding another smoke suite.

Remaining acceptance: build the exact commit through the pinned container,
install its signed APT package on a fresh aarch64 standard-prefix Termux
device, run the installed-bundle validator, complete one authenticated model
turn, perform file/terminal operations, load a skill/plugin/MCP service,
start/stop a gateway with an allowlist, restart under an alternate
`HERMES_HOME`, and upgrade from a recorded prior APT release while preserving
state. Record device/Android version, package version/hash, logs and exit
codes. The mixed PRoot source workflow failure above does not substitute for
this acceptance. The warning remains.

## Security review scope and findings

This is a targeted code-path review, not an exhaustive penetration test.
No new first-party boundary-crossing exploit or OS isolation escape was
established by the inspection. Public dependency advisories are recorded in
the resumed receipts below. This is not a security certification. No private §3.1 finding is
being published in this report.

| Surface | Code path and interpretation |
| --- | --- |
| Terminal and remote backends | `tools/terminal_tool.py`, `tools/environments/`: terminal/file confinement depends on the selected backend's actual mounts, identity and remote policy. Local execution has the user's reach. |
| File reads/writes | `agent/file_safety.py` classifies credential paths, profile roots, resolved targets and directory entries; it separates denied writes from approval-required paths. `tools/file_operations*` consumes these policies. This cannot contain a hostile shell permitted to reach the same files. |
| Sandbox mirrors | `classify_sandbox_mirror_target` and container mirror guards prevent accidental writes into non-authoritative copies; they are soft guards, not isolation. |
| Approval/YOLO | `tools/approval_context.py` binds session/turn identity and defaults unattended/cron decisions to deny. `approval_yolo.py` centralizes session restore/carry. YOLO intentionally bypasses approval policy; it confers no external device authorization. |
| Child credentials | `tools/environments/local.py::build_subprocess_env`, `tools/code_execution_env.py`, MCP config/transport and `cron/scheduler_script.py` scrub child environments with declared exceptions. In-process plugins can still read the agent's credentials. |
| MCP/plugins/skills | MCP launches host-side subprocesses; plugins load in process. Install review and supply-chain checks matter. A sandboxed terminal alone does not contain these paths. |
| Browser/computer use | Browser URL/redirect policy lives in `tools/browser_tool.py`; computer-use permissions must remain session scoped. Browser cookies, vault state and device access inherit the process's trust envelope. No live browser/device exercise was completed by code inspection. |
| Subagents | `tools/delegate_tool.py` derives child depth/toolsets, resolves runtime/provider overrides, and opens a child session. Shared host credentials/process privileges are not reduced merely by delegation. |
| Cron | Scheduler binds owner/profile scope, checks credential routing and uses sanitized script environments. Scheduling is not an authorization escalation grant. |
| Gateways/webhooks | `gateway/run_inbound.py` authorizes before pause-state handling; webhook ingress/delivery re-check route authorization. Session IDs are routing handles. Each exposed adapter still requires configured authorization. |
| Secret storage | Profile-aware credential paths, private writers and redaction reduce accidents. `SECURITY.md` remains authoritative: full-process OS wrapping is the containment posture for untrusted inputs. |

Future VoidForge privileges must live in a separately authenticated service,
ideally a separate OS principal/device-side authority. A project manifest,
model decision, BLHermes approval, plugin installation, Codex worker, or YOLO
flag must never imply permission to flash, wipe, unlock or otherwise destroy
device state. The external service must independently validate caller,
device identity, operation, scope and explicit user authorization.

## Proposed project architecture (design only)

Start with project-owned metadata plus a skill invoked through existing tools.
Keep integration code in a standalone plugin repository when it has a concrete
consumer. Do not add a core project tool or generic framework now.

Reuse the existing profile-owned registry in `hermes_cli/projects_db.py`
(`projects.db`), its `hermes project` CLI in `projects_cmd.py`, and the
profile-scoped RPC methods in `tui_gateway/methods_projects.py`. It already stores
IDs, unique slugs, names, multiple folders, a primary path, archive state and a
kanban board binding. Desktop consumes it through `src/store/projects.ts`.
Do not introduce a second `projects.yaml` registry or a duplicate project tool.

A proposed repository-owned `.blhermes/project.yaml` adds portable project intent,
resolved relative to an existing registered folder. This manifest is not
implemented by the audit. Initially a skill can read it with existing file tools;
any later plugin-specific local overrides should key on the existing project ID
and remain profile scoped. Repository metadata is untrusted input: reading it
must not execute commands or install plugins automatically. Machine-specific
paths belong in local state, never secrets in repository metadata.

Suggested manifest fields:

```yaml
schema_version: 1
project_id: axiom-launcher
project_type: android-app
commands:
  build: ["./gradlew", "assembleDebug"]
  test: ["./gradlew", "testDebugUnitTest"]
  lint: ["./gradlew", "lintDebug"]
invariants: ["Preserve the documented launcher lifecycle contract."]
release_standards: ["Record commit, artifact hash, tests and signing owner."]
skills: []
plugins: []
mcp_services: []
knowledge_paths: ["docs/architecture.md", "docs/decisions/"]
```

The existing project registry supplies repository paths; command argv, working directory,
timeout and expected artifacts should be validated before execution. Commands
are proposed actions, never execution grants. VoidForge would use its own
project type and authenticated external service rather than launcher-specific
core branches. VOID.SYS, AXIOM Shooter and future projects use the same portable
metadata without importing their code into BLHermes.

Use existing `agent/prompt_builder.py` startup CWD context, project AGENTS.md,
`skill_view`, file/terminal tools, project/user plugin discovery,
`PluginContext.register_cli_command`, existing memory-provider APIs, and
configured MCP servers. Select profile, project, skills and tool surface at
session creation. Pin a manifest digest and repository revision in task context.
During a conversation, append fetched metadata/knowledge as tool results;
do not rebuild the system prompt, reload memory or swap toolsets. A project
switch creates a fresh session; queued config changes apply to the next one.
Persist reviewed decisions with source/revision and project/profile scope.
Do not treat a memory entry as executable policy or authorization.

## Codex orchestration proposal (design only)

The code already distinguishes two integrations:

* `agent/transports/codex.py`, `agent/codex_responses_adapter.py`, and
  `agent/codex_runtime.py` implement Codex Responses requests/streaming while
  BLHermes owns its loop and tool dispatch.
* `agent/transports/codex_app_server.py` owns the CLI subprocess protocol;
  `codex_app_server_session.py` owns one Codex thread per BLHermes session,
  turn/cancellation/approval handling, and permission-profile mapping.
  `codex_event_projector.py` mirrors streamed events into BLHermes messages.

`agent/codex_runtime_history_seed.py` seeds prior history only for fresh
threads; resumed threads already own it. `conversation_compression_codex.py`
compacts the provider-owned thread and leaves the BLHermes transcript mirror
unchanged. Usage anchoring and failure cooldowns already exist. Rewriting
only the mirror would not compact the actual Codex context.

`hermes_cli/codex_runtime_switch.py` and migration siblings manage existing
runtime selection/configuration. `agent/transports/hermes_tools_mcp_server.py`
is an existing callback bridge. Reuse these deliberately; do not migrate MCP
servers into a worker implicitly or duplicate tool access.

For a specialized coding worker, first exercise existing delegation runtime
overrides (`tools/delegate_tool.py`) against the intended Codex route. Keep
the BLHermes parent responsible for planning, task boundaries, project memory,
verification and acceptance. Give the worker a bounded goal, isolated worktree,
allowed tools, base commit, commands and artifact contract; retain task/thread
IDs and interrupt/failure state. A worker completion is input to verification,
not evidence that tests passed. Persist approved knowledge only after checking
the actual diff and command receipts.

Official OpenAI guidance distinguishes `codex exec` for bounded jobs, SDK
integration for programmatic workflows, and app-server for persistent turns,
events and approvals. This supports reuse of the existing app-server path
where lifecycle control is needed; it does not prove this fork's live account
or model access. See [Codex as a platform](https://developers.openai.com/blog/codex-as-a-platform).

## Next pass and release gates

1. Resolve the reproducible bootstrap/environment failure and obtain complete
   Python/JS validation receipts on a clean supported host.
2. Reproduce failures in isolation before patching; keep behavior-contract
   tests and avoid broad suppressions or dependency upgrades as a workaround.
3. Validate a built Termux package on a real device and establish the warning's
   actual cause before changing support claims.
4. Provision fork-owned release runners, artifact/signing infrastructure and
   update ownership before publishing packages under a fork identity. Current
   Nous endpoints are upstream infrastructure, not BLHermes-owned services.
5. Only then trial project metadata plus a skill with one concrete project,
   and test existing Codex delegation before considering a new plugin.

A green source lint run alone cannot certify packaging, provider accounts,
gateways, Desktop, Android, remote backends, or authorization boundaries.

## Resumed pass: branding and validation receipts (2026-10-22 UTC)

The resumed checkout already contained the earlier pass's uncommitted branding
changes and this report. Those changes were reviewed and extended, rather than
attributed to the two original fork commits. Product prose, comments, notes,
CLI/UI messages and text/vector labels now use BLHermes across the tree.
The CLI's default large text logo now says BLHERMES AGENT. Compatibility names
remain intentional: `hermes`, `hermes_cli`, `HermesCLI`, `HERMES_*`, `.hermes`,
wire/storage identifiers, distribution names, model IDs, upstream URLs and
release identities. Frozen historical compatibility fixtures, legal notices,
third-party names and existing binary artwork are not a migrated product ABI.
This is a product branding pass, not a complete package/namespace or artwork
migration. Do not apply a blind case-insensitive replacement to these names.

README now explicitly distinguishes the fork from upstream installer/feed/hosted
documentation services. Termux warnings are repeated in all four READMEs;
the detailed warning remains. Fork-owned release infrastructure is still a
release blocker. No Outer-Void integration, project manifest loader, new core
tool, provider, plugin or permission policy was implemented.

One tooling defect was fixed: `scripts/run_tests.sh` used `compileall -j 0`
before the test runner, ignoring a user's `-j 1` test-worker cap. That warmup
could fan out across every CPU on this constrained phone. It now compiles
sequentially (`-j 1`); per-file isolation, test selection, retries, credential
scrubbing and failure propagation are unchanged. The existing runner canary
passed through the canonical runner after this change. No lint rule, security
check or test was disabled.

The validation environment reused the disposable PM-provisioned application,
test and Ruff environments from the earlier pass. Tool versions were verified:
Python 3.14.7, Ruff 0.15.10, Node 26.7.0, npm 12.0.2. The workaround is a
PM-provisioned glibc interpreter, not a claim that normal activation works on
this proot host. No raw pip/uv dependency mutation was performed.

### Python commands and results

The original `python scripts/check` attempt failed on an audit-report literal
temporary path. The report was corrected. To respect the requested concurrency
limit, the resumed run invokes the same twelve checks **one at a time**:

```sh
for baseline_check in footguns shebangs no-tmp config-writers os-marker-fakes agents-md case-collisions lazy-deps profile-archives blob-size ruff health; do
  python scripts/check --only "$baseline_check"
done
```

The focused regression command was:

```sh
scripts/run_tests.sh -j 1 --file-retries 0 --file-timeout 120 \
  tests/scripts/test_run_tests_shell.py \
  tests/hermes_cli/test_banner.py \
  tests/hermes_cli/test_banner_distribution_label.py \
  tests/hermes_cli/test_banner_release_channel.py \
  tests/hermes_cli/test_plugin_api_compat.py \
  tests/agent/test_codex_runtime_history_seed.py \
  tests/agent/test_codex_app_server_compaction.py \
  tests/agent/test_file_safety.py \
  tests/agent/test_file_safety_write_credentials.py \
  tests/agent/test_file_safety_cross_profile.py \
  tests/agent/test_file_safety_sandbox_mirror.py \
  tests/scripts/test_termux_agent_assembly.py \
  tests/scripts/test_termux_build_wheels.py \
  tests/scripts/test_termux_launchers.py \
  tests/scripts/test_termux_python_linkage.py \
  tests/scripts/test_termux_retag_wheel.py \
  tests/scripts/test_termux_update_refusal.py \
  tests/test_scratch_scan_failures.py \
  tests/test_scratch_prune_undeletable.py
```

Result: **19 files, 79 passed, 0 failed, 1 skipped**, exit 0, 193.7 seconds.
The skip does not establish coverage for another host.

Earlier receipts remain relevant and are not hidden by this passing subset:

* A 15-file targeted run with two workers completed with **165 passed,
  6 failed, 1 skipped**. All six failures were in `tests/test_scratch_dir.py`,
  involving process ownership/liveness, cleanup, subprocess waits or filesystem
  timestamps. A subsequent run timed out after 300 seconds with 29 progress
  dots. Their cause has not been isolated on a supported native host; they
  remain unresolved, not waived as harmless proot differences.
* Full-suite attempts discovered 6,569 files (about 49,712 tests). The latest
  saved full attempt stopped after 111 passing tests with a `timeout` wait/write
  “Function not implemented” error. These interrupted receipts are **not** a
  full-suite pass. The resumed focused command deliberately uses neither that
  timeout wrapper nor multiple test workers.

### JavaScript, packaging and security acceptance

`npm ci --foreground-scripts` succeeded (exit 0), including building the native
`node-pty` extension and Electron's installation. This supersedes the earlier
interrupted root installation and its missing-`tsc` failures. It does not prove
that the Electron application can launch on this host.

The successful root install reported **20 advisories: 8 low, 8 moderate,
2 high, 2 critical**. The earlier successful website install reported
**47 advisories: 3 low, 13 moderate, 14 high, 17 critical**. Counts refer to
separate installed graphs at their recorded times and must not be added or
presented as confirmed exploitable product vulnerabilities. No automatic
`npm audit fix` or dependency-policy relaxation was performed.

Live provider authentication/turns, network gateways, browser/computer-use
sessions, remote backends, desktop install/update E2E, signed native packages,
Windows/macOS behavior, and real native-Termux bundle operation have not been
certified by these source tests. They require separate acceptance receipts.
In-process approval and YOLO remain heuristics; privileged future services must
independently authorize destructive operations as described above.

The root audit's high/critical paths include the direct Electron runtime and
`simple-git` (used by `apps/desktop/electron/git-review-ops.ts`), plus transitive
`extract-zip` and `@simple-git/argv-parser`. Public advisory examples:
[Electron guest-window restrictions](https://github.com/advisories/GHSA-9f4c-93c8-jc8g),
[simple-git configuration handling](https://github.com/advisories/GHSA-g4wm-2vf7-vfgr),
and [extract-zip symlink handling](https://github.com/advisories/GHSA-7pqw-9j4j-h8q3).
This establishes affected dependency declarations, not a new private exploit.
The audit suggests a same-major Electron patch and a major simple-git migration;
those require reviewed manifest/lock changes and native Desktop regression
coverage. They were not applied unverified on this phone. Prioritize this
work before any Desktop release or untrusted-repository deployment.

Workspace results: `npm run build:ink --workspace ui-tui` passed;
`npm run --ws lint` passed (exit 0) with warnings (not compared against a base scan), including 295 in
Desktop, 14 in TUI, and 28 in web. `npm run --ws typecheck` exited 134 because
Desktop's first TypeScript process exhausted Node's default heap at about
2 GiB. The bootstrap installer, shared, TUI, Ink, web and root-tests
workspace type checks completed without reported errors. No compiler settings
were relaxed and no larger heap was forced on this constrained device.

Of the twelve sequential `scripts/check` checks, eleven passed. `health`
failed to finish its comparison before the command's existing **900-second**
timeout (`subprocess.TimeoutExpired`, exit 1). This is an incomplete
measurement, not zero findings and not a passed lint lane. A complete
code-health receipt on the final commit is still required on a supported host.

## Completion pass (2026-10-22 UTC)

The continuation recovered the saved logs and PM environments rather than
starting provisioning again. `git ls-remote origin refs/heads/main` still
reported the initial fork HEAD, `661cd4900af6b1d658f4d7fec3390a220af3dd36`.
The saved upstream observation, merge base, and 2/7 divergence above were
rechecked locally. They are not a new fetch of upstream main.

The remaining branding review updated missed plain-language messages,
comments, docstrings and translations, including hyphenated product prose.
Matching UI assertions were updated as well. Windows service instructions
retain the literal `Hermes*` naming rule because production still recognizes
`normalized_name.startswith("hermes")`; changing this example to `BLHermes*`
would have made the instructions false. Protocol/header names, Python/JS
namespaces, package/executable/artifact identities and actual model names stay
compatible. Historical fixture payloads, third-party quotations, legal credits
and existing binary artwork are not evidence of a completed namespace or
artwork migration. The requested broad textual rebrand increases future merge
conflict risk even where runtime behavior is unchanged.

Review found an unverified scratch-cleanup experiment left by the stalled
run (UID selection and directory-entry classification). It was restored to
the base behavior; scratch-module changes in this deliverable are branding
only. This does not fix or waive the six previously recorded scratch failures.
No accidental/dead module was established and none was deleted.

The existing `website/scripts/prebuild.mjs` is now registered as
`prebuild:fast`, so the documented fast build invokes the same catalog/index
preparation as the normal build. This changes no dependencies. The earlier
website build log ends during webpack compilation without an exit receipt;
it must be classified as incomplete. Likewise the saved `ty` output is empty
and supplies no completed Python type-check result.

The full TUI command below completed with **236 files passed, 1,853 tests
passed, 2 skipped**, exit 0, 591.36 seconds:

```sh
npm run test --workspace ui-tui -- --maxWorkers=1 --no-file-parallelism
```

Its stderr included a missing `ruamel.yaml` import in a Python subprocess.
The suite still returned success, so this is a limitation of that receipt,
not a claim that every Python-backed path worked. Subsequent targeted JS
commands put the PM test interpreter's bin directory first on PATH:

```sh
export PATH="$(dirname "$HERMES_PYTHON"):$PATH"
```

No live OpenAI account was exercised. The Codex proposal was rechecked using
the OpenAI Docs skill and the fetched official
[Codex platform documentation](https://developers.openai.com/blog/codex-as-a-platform).
The persistent-thread/event/approval integration described there supports
reuse of this repository's existing app-server adapter. Account access,
worker delegation behavior and effective permissions still need live testing.

The final Python regression command used the 19-file list above plus
`tests/hermes_cli/test_skin_engine.py`, with the same `-j 1 --file-retries 0
--file-timeout 120` options. Result: **20 files, 91 passed, 0 failed,
1 skipped**, exit 0, 401.4 seconds. This receipt was collected after restoring
the original scratch behavior. It covers scan/permission contracts, not the
previously failing full `test_scratch_dir.py` file.

```sh
npm run test:ui --workspace apps/desktop -- --maxWorkers=1 --no-file-parallelism \
  src/themes/classic-skin.test.tsx src/components/boot-failure-overlay.test.tsx
```

Desktop UI result: **2 files, 24 passed**, exit 0, 79.05 seconds. This is a
jsdom regression receipt, not a native Electron install/update or security
acceptance test. `git diff --check` also passed; Git emitted only the existing
PowerShell LF/CRLF normalization notices.

```sh
npm run test --workspace ui-tui -- --maxWorkers=1 --no-file-parallelism \
  src/__tests__/createGatewayEventHandler.test.ts \
  src/__tests__/brandingCanonicalSnapshot.test.ts \
  src/__tests__/brandingMcpCount.test.ts
npm run prebuild:fast --prefix website
```

The final affected-file TUI rerun passed **3 files / 111 tests**, exit 0,
13.73 seconds, with the PM test interpreter first on PATH. These overlap the
full TUI suite and must not be added to it as distinct coverage. Website
prebuild passed, exit 0: skill/plugin catalogs, automation blueprints and
LLM documentation indexes were generated. Generated site data remains ignored
build output and is not included in the source commit.

The optional plugin host mode (`plugins.isolation: host`) is a separate process
and IPC surface; its presence alone does not establish an OS sandbox or a
reduction in the host user's authority. Whole-process isolation and independent
authorization for future privileged services remain required as described
above. No security policy, approval gate, environment scrubber or plugin API
was weakened by this pass.

The final sequential guard run passed **11/11**: footguns, shebangs, no-tmp,
config-writers, os-marker-fakes, agents-md, case-collisions, lazy-deps,
profile-archives, blob-size and pinned Ruff. The twelfth lane, code health,
retains its earlier 900-second timeout and is not counted as passed. Running
the checks separately controls concurrency; it does not relax their rules.

### Validation and release-readiness matrix

| Category | Evidence / remaining gate |
| --- | --- |
| Environment/setup | PM-built disposable interpreter/tools reused successfully; normal activation's PRoot path-identity failure remains. No raw pip/uv mutation. |
| Python lint | Pinned Ruff and ten other short guards pass on the completion tree. Code-health comparison remains incomplete. |
| Python static/types | Earlier `ty` attempt has no completed result; rerun the CI comparison on a supported host. |
| Python tests | Final 91-pass regression receipt; full suite incomplete; six earlier scratch failures unresolved. |
| JS/TS lint | Workspace lint passed with warnings in the earlier resumed receipt; commit hooks also judge staged source. |
| TypeScript | Smaller workspace checks passed previously; Desktop exhausted its default heap. No settings relaxed. |
| TUI tests | Full 236-file suite passed, plus affected-file rerun after the final edits; Python-subprocess stderr limitation described above. |
| Desktop | Selected UI contracts pass; full unit/native/install/update E2E and Desktop typecheck are not certified. |
| Packaging/platforms | Termux source contracts pass with a host-specific skip; signed packages and native Android/Windows/macOS acceptance remain. |
| Documentation/build | Website prebuild passes; earlier production build has no completion receipt. Existing Ink build passed. |
| Security/dependencies | Targeted boundary review and file-safety tests; public npm advisories remain unresolved. No live penetration-test claim. |

**Baseline status: audited, partially verified, not release-ready.** Obtain a
complete full-suite/code-health/typecheck/site-build receipt, isolate the
scratch failures, review dependency advisory remediation, establish fork-owned
release infrastructure, and validate the signed native Termux package before
calling this a reliable release baseline. Live providers, Codex delegation,
gateways, browser/computer use and remote backends need separate acceptance.
Project metadata and Outer-Void integration remain design-only.

```sh
npm run test --workspace web -- --maxWorkers=1 --no-file-parallelism
```

Dashboard result: **65 files, 449 passed**, exit 0, 203.23 seconds. jsdom
emitted unimplemented canvas/window warnings and Node emitted experimental
localStorage notices; this receipt does not verify real browser rendering.
The final documentation review also restored the upstream Hermes 2/3/4 model
family names accidentally rebranded by the earlier run. Those are model
identities, not BLHermes branding; restoring the English model heading also
preserves its existing in-page anchor.

The first commit attempt was correctly blocked by the pre-commit hook's
bootstrap-installer lane: three import-order errors in
`apps/bootstrap-installer/vite.config.ts`. The same unsorted imports exist in
the base version. The normal workspace lint command had not caught this
config-file path. Imports were sorted (no runtime/config behavior changed),
and the explicit ESLint check and complete commit hooks were rerun. Hooks
were not bypassed; the initial hook failure is retained in the raw log.
