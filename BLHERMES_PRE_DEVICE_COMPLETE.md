# BLHermes pre-device completion handoff

Engineering handoff for the commit containing this report. Build that committed
checkout; do not attribute a production artifact to the historical input commit
`1e6c382569fa`. The exact final SHA is `git rev-parse HEAD`.

## 1. Source status

**SOURCE COMPLETE — BUILD ENVIRONMENT REQUIRED**

**NO KNOWN PRE-DEVICE IMPLEMENTATION BLOCKERS.** No known Termux implementation
P0/P1 remains from this pass. Production installation remains unsupported until
the actual package and Android acceptance gates pass. This is scoped Termux
source completion, not whole-repository or device certification.

## 2. Known code defects

Corrected in this pass:

- Wheel export selected ACP alone instead of the declared Termux baseline,
  omitting MCP/cron requirements. Export now selects `termux` through PM.
- Auditor rejected the **pinned static AArch64 rg** for lacking a dynamic loader.
  Reproduced against the actual pinned host copy; only static rg has an exception.
- APT index omitted dependency relationships. It now preserves them; package
  metadata declares Termux-owned `ca-certificates` rather than pretending trust
  roots are bundled. Wrong-architecture indexes are refused.
- Launcher environment failures were opaque under `set -u`. Android launchers
  validate HOME/PREFIX/HERMES_HOME/TMPDIR and supply documented shell/locale hints.
- Full Git snapshots carried tests and source-only frontends into the package.
  Assembly trims inert trees after planting the built TUI, preserving runtime scripts.
- Malformed tar payloads produced an operator traceback instead of a concise
  rejection. The CLI now reports the archive failure without executing content.
- Archive links could be cyclic or have normalized absolute escapes; RPATH accepted
  origin lookalikes. Auditor rejects these, linked parent members, special modes/types,
  nonregular runtime entrypoints and explicit glibc SONAMEs.
- Native import gate could accept packages' pure Python fallback. Known fallback
  distributions now import their actual extension modules.
- MCP and execute_code filtering dropped bundled Bionic loader paths. A platform adapter now
  reconstructs package-owned paths from bundle metadata, without forwarding
  arbitrary parent loader overrides or provider credentials. The local MCP probe
  exercises the production environment/resolver path.
- Canary tag admission accepted impossible calendar timestamps; it now rejects them.

## 3. Known platform limitations

Only unrooted standard-prefix com.termux, aarch64 / arm64-v8a is targeted.
Wheel target android_24_arm64_v8a, CPython cp314. API 24 is a build target;
minimum supported Android/Termux versions are unqualified. No root/Magisk/ADB,
PRoot, shared-storage permission or Termux:API is required for base operation.
Android may suspend/kill foreground/background work; cron and gateway are not
promised durable while Termux is suspended. Local Electron/Chromium/Docker,
nemo-relay and native phone clipboard/image/audio integrations remain unqualified.
Native third-party plugins/MCP executables need Android-compatible dependencies.
Rolling builder compiler packages prevent a bit-for-bit reproducibility claim.

## 4. Test matrix

| Gate | PASS | FAIL unresolved | SKIP / NOT RUN |
| --- | ---: | ---: | --- |
| Python source contracts, latest per-file/case receipts (45 files) | 696 distinct cases | 0 | 8 cases |
| TUI layout/input/picker/terminal/clipboard/URL (10 files) | 144 cases | 0 | 0 |
| Short guards + Ruff + code health | 12 lanes | 0 | 0 |
| Final auditor adversarial suite (included above) | 19 cases | 0 | 0 |
| Final acceptance/bundle suite (included above) | 12 cases | 0 | 0 |
| APT signing/tamper suite (included above) | 14 cases | 0 | 0 |
| Full gateway config completion retry (included above) | 93 cases | 0 | 0 |
| Python/shell syntax; 38 local links / 31 shell blocks | PASS | 0 | 0 |
| Production build/audit/Bionic/installed/device | 0 | 0 | NOT RUN: external environment/artifact required |

The eight skips are two Docker ownership cases, one unavailable host shared
libpython case, two staging cases for other host targets, one macOS bind case
and two Windows native-environment cases. They are not passes. Counts exclude
duplicate reruns. Provider classification covers 191 unchanged passing cases
plus the separately rerun repaired fixture (1); it is not a new single 192-pass
run. All 51 related welcome-route cases pass. Initial failures/timeouts and
repairs are retained in the release ledger. Full repository suite was not run.

**44 regression cases added**, plus stronger existing assembly assertions and
three corrected upstream wire-message fixtures. The live process-tree test uses
the fixture's documented signal opt-in for its own freshly spawned children;
assertions and production cleanup remain intact. Logs and the detailed per-file
matrix live in ignored `.build/termux/qualification/`; no private state is attached.

## 5. Documentation status

English/Spanish/Chinese/Urdu README notices point to this handoff. End-user
contracts and upstream migration are in [docs/termux.md](docs/termux.md).
Operator build/signing/schema/publication rules are in
[scripts/termux/README.md](scripts/termux/README.md). The
[device worksheet](docs/termux-device-acceptance.md) retains manual acceptance
and includes the automated offline driver. Historical baseline is unchanged.

## 6. Migration status

Read-only stale-source detection reports filenames without source URLs.
The observed upstream 404 and exact grep command are documented. Only the
identified entry/file and an independently identified unused key may be removed
by the operator. No automatic APT edits. Same `hermes-agent` identity means dpkg
replacement, not coexistence. Manual/source launchers may shadow PATH; foreign
prefix launchers are refused. Existing user profiles are reused when selected;
back up privately and accept against isolated state first.

## 7. Packaging status

Package-owned fixed-prefix runtime and user-owned profile/cache/credential data
are documented separately. Maintainer scripts make no network calls and never
erase state, including on purge. Synthetic install/remove/purge/reinstall checks
preserve representative state. dpkg owns updates; self-update refusal retained.
Node/npm (implementation tooling), FFmpeg, rg and uv remain bundled and verified.
No source-checkout cwd/PYTHONPATH is required by generated launchers. Runtime
probe checks compression/hash/readline, TLS trust, SQLite restart, ctypes, Unicode,
temp files, threads, asyncio, multiprocessing, subprocess and signals.

## 8. Build environment requirement

A **native aarch64 Linux/glibc host with working Docker daemon**, pinned PM
Python/Node and documented build tools. Current PRoot host has no Docker client
or daemon. Installing a client alone does not provide the required environment.
Good build gates were not bypassed or changed to produce host binaries.

## 9. Artifact status

No production artifact, measured package size or candidate hash. Schema-v1 release
summary is implemented with all required fields; unavailable values are null and
unexecuted evidence pending. Assembly emits the real audited summary only after
the mandatory Bionic/installed gate. Sidecar audit hashes must agree. Old receipts
are removed before replacing package bytes. CI retains release JSON with deb/audit.

## 10. Device acceptance preparation

Installed validator checks package identity/architecture, isolated CLI/ACP,
package-local backend imports, native wheels, tools, discovery, updater refusal,
and PTY setup at 120×30, 100×30, 80×24, 60×24, 50×20, 40×20 with child cleanup.
A bundled constant-only MCP fixture and real stdio probe need no external service.
`device_acceptance.py --safe --output NEW.json` runs offline checks in disposable
state and creates a private facts-only bundle with PASS / FAIL / SKIP. It refuses
host Linux as device evidence, never changes packages or enters credentials, and
never collects configuration, environment dumps, conversations or app logs.

## 11. Security status

No approval, secret scope, gateway auth, tool policy or OS isolation boundary was
weakened. Archive checks are release-input hardening under SECURITY.md §3.2;
no new §3.1 boundary-crossing finding is asserted. The diagnostic deliberately
omits private logs instead of promising perfect redaction. Plugin/MCP code still
runs with the user's authority. Host tests are not a security certification.

## 12. Public APT status

NOT PROVISIONED. No URL/fingerprint invented. Existing signer verifies both
signatures with an isolated disposable keyring; index/checksum/by-hash and tamper
contracts are tested. Operator docs specify independent fingerprint publication,
protected key, stable/optional canary, atomic snapshot publication, immutable pool
and rollback. Real signed N→N+1 acceptance needs two genuine packages and a feed.
Release CI explicitly fails missing native infrastructure; PR checks do not publish.

## 13. Only remaining unproven items

No known deterministic implementation failure remains. Environmental gates are actual production
build/audit/Bionic install and real package sizes; Android gates are device
install, keyboard/rotation/lifecycle, authenticated streaming/cancellation,
real terminal/file work, reviewed integrations, gateway authorization, state
usability and genuine signed upgrade/remove/reinstall. None are inferred from mocks.

## 14. Exact next action

Move the final committed checkout to a native aarch64 Linux/glibc host with
working Docker and the documented pinned PM tools. The current build attempt
exits 1 with `missing build tool: docker`; no artifact is produced. Run:

```sh
python3 scripts/termux/build.py --prepare --repo . \
  --commit "$(git rev-parse HEAD)" \
  --payload .build/termux/payload --out .build/termux/deb
```

After all package gates pass, supply the exact archive/hash/receipts to the
safe device driver and manual worksheet. Only real successful Android acceptance
permits TERMUX RELEASE ACCEPTED.

## Requirement evaluation map

| Mission sections | Implementation / validation authority |
| --- | --- |
| 1–5, 40–43 | Existing build/runtime code and history inspected; targeted path/marker scan; inert payload trimming; real static-rg audit reproduction; pinned graph/image/artifact hashes retained. Builder/CI/remote Linux paths remain intentional. |
| 6–7, 9–10, 28–30 | Launcher and isolated-state/lifecycle tests; explicit environment/state/collision contracts; safe foreign-launcher refusal; package update ownership. |
| 8, 38 | Read-only migration diagnostics and end-user instructions; all maintained README notices synchronized. |
| 11–14, 16 | Runtime probe, native-extension gate, PM/Bionic/linkage/wheelhouse contracts and installed tool checks. Native execution remains external evidence. |
| 15, 39 | Existing provider config/error/cancellation regressions; actionable runtime/TLS/launcher/validator errors. Real provider behavior remains device acceptance. |
| 17–19 | Optional integrations remain optional; browser URL/manual fallback and unsupported clipboard behavior documented; TUI clipboard/open-url regression tests. |
| 20–21 | Host layout/input/status/picker/terminal tests plus six installed PTYs; process-tree cleanup contract; real keyboard/signals/lifecycle worksheet. |
| 22–24 | Existing malformed/discovery/plugin-gating/MCP failure contracts; real local MCP fixture, native dependencies gated by target; installed discovery gate. No certification of every plugin. |
| 25–26 | Existing gateway bind/auth/config/rebind/port-conflict and scheduler restart/catchup tests; foreground Android lifecycle contract. No public default bind or systemd added. |
| 27, 31–32 | Debian calendar/version ordering, metadata propagation, adversarial archive tests; installed validator machine gate. |
| 33–37 | Safe offline acceptance/bundle, release-summary schema, signed staging/tamper contracts, CI release prerequisites and artifact retention. |
| 44–50 | Final test/build receipts and classification below and in release ledger; committed/pushed handoff. |
