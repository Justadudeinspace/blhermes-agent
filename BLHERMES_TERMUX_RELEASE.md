# BLHermes Termux release ledger

Engineering receipt for the commit containing this document, 2026-10-22.
Historical baseline remains in [BLHERMES_BASELINE.md](BLHERMES_BASELINE.md);
the previous candidate pass is preserved at Git commit `1e6c382569fa`.
The [pre-device handoff](BLHERMES_PRE_DEVICE_COMPLETE.md) records scope, fixes,
requirement evaluation and operator continuation.

## Status by evidence layer

| Layer | Status |
| --- | --- |
| Implementation | **SOURCE COMPLETE — BUILD ENVIRONMENT REQUIRED** |
| Build | BLOCKED — REQUIRED AARCH64 LINUX + DOCKER BUILD ENVIRONMENT UNAVAILABLE |
| Artifact | NONE — no production deb, candidate hash or measured sizes |
| Bionic | NOT RUN — production interpreter/container unavailable |
| Installed package | NOT RUN — production package unavailable |
| Device | NOT STARTED |
| Public distribution | NOT PROVISIONED — no BLHermes URL/fingerprint/feed identity |
| Production support | UNSUPPORTED pending real release/device gates |

## Source and build provenance

Initial source: `1e6c382569fa` on clean `main`. No recovered user edits existed.
Final source is the commit containing this ledger; `git rev-parse HEAD` gives
its exact SHA. The package builder archives a selected committed tree, never
mixes dirty application code into a release, and preserves strict native gates.

Current host: Debian aarch64/glibc under PRoot on an Android kernel. This is
not a supported native Docker builder or a packaged Android acceptance runtime.
Existing isolated PM Python 3.14.7, Node 26.7.0 and pinned lint/test environments
were reused without raw pip/uv mutation. Test processes use isolated HERMES_HOME.
No more than two long-running command lanes were used; Python runners use `-j 1`.

Actual production build attempt:

```sh
python3 scripts/termux/build.py --prepare --repo . \
  --commit "$(git rev-parse HEAD)" \
  --payload .build/termux/payload --out .build/termux/deb
```

Exit **1**, `missing build tool: docker`, before payload staging. No Docker
client/daemon/socket or external builder is supplied. **BUILD BLOCKED BY
ENVIRONMENT**. Installing a client inside PRoot is insufficient. Repeat on the
final committed tree and retain `.build/termux/qualification/pre-device-build.log`.
No build code was changed to bypass native infrastructure or emit host binaries.

## Implementation changes

PM now exports the declared Termux baseline including MCP/cron/ACP. Transient
wheel-inventory failures stop the build; native classification is sorted and
hash-bound. Native import checks load known extension implementations instead
of silently accepting pure-Python fallback. The pinned static AArch64 ripgrep
is accepted under a narrow, inspected static-ELF rule; other runtime binaries
still require Android's dynamic linker. Actual pinned-rg rejection was reproduced
before correction, with before/after logs retained.

MCP and execute_code child filtering now compose package-owned Bionic loader paths through a
platform adapter, preserving credential filtering and ignoring arbitrary parent
loader overrides. The local fixture uses the real production launch seam.
Launcher environment validation/defaults, compression/hash/readline and TLS
probe coverage, package-local imports, six PTY dimensions, a real local MCP
fixture, PASS/FAIL/SKIP diagnostics and a safe offline acceptance driver are ready.
User state remains outside package ownership. Representative synthetic profile
data survives maintainer-script install/upgrade/remove/purge/reinstall.

Assembly removes inert source/test/build/frontend trees after built products are
planted. Auditor rejects unsafe/cyclic/dangling links, linked-parent members,
privileged/special types, nonregular runtime commands, origin lookalikes/escapes,
wrong layout/identity/architecture and glibc linkage. APT staging preserves
package dependencies, rejects malformed ar and wrong architecture; the package
declares ca-certificates as a Termux-owned prerequisite. Canary calendar timestamps
are checked. Old package receipts are cleared before replacement. Schema-v1
release summaries are emitted after mandatory container validation; pending
measurements are null, not invented. CI retains summaries and explicitly fails
missing release infrastructure.

## Host verification receipts

Final source coverage: **45 Python files, 696 distinct passing cases, 0 unresolved
failures, 8 explicitly skipped cases**. This is the union of the latest relevant
per-file/case receipts, not one monolithic run; duplicate reruns are excluded.
The detailed machine matrix is `.build/termux/qualification/pre-device-test-matrix.json`.
See the [handoff test table](BLHERMES_PRE_DEVICE_COMPLETE.md#4-test-matrix).
All 12 guard lanes pass. Final Ruff passes; final health reports **28 measured
files, 0 blocking, 0 advisory**. Python/shell syntax and whitespace pass.
Documentation: **38 local links and 31 shell blocks pass** across the guides,
ledger, handoff and four maintained READMEs; no external-link/site-build claim.

Initial broad matrix: 35 files, 329 passed, 1 failed, 5 skipped. The new MCP
probe used the old SDK field spelling (`isError`); corrected to pinned `is_error`,
then verified through a real stdio fixture using production child environment
resolution. The new plugin fixture's cleanup initially called a nonexistent
`unload_all`; corrected to the actual `unload` API, then passed. An initial
health check rejected a new test conditional ladder; replaced with table dispatch.

The full provider file completed **191 passed, 1 failed**. History identified
the failure as an earlier branding edit to a server wire-message fixture, not
a reason to broaden the parser. Restored upstream “Hermes Agent” text in all
three matching fixtures. The repaired classifier case passes separately;
all **51** related welcome identity/recovery cases pass. Production provider
classification behavior and assertions were not weakened.

Two initial broader files exceeded a 180-second host limit. Gateway config
subsequently completed all 93 assertions near its 900-second deadline but the
runner killed it before process completion; that is not counted as a clean run.
The final **1800-second-limit retry passed all 93 and exited 0** (1007.7 s).
Provider classification completed within its longer limit. A stack sample
showed repeated secure-state initialization under PRoot; security checks were
retained. The process-cleanup fixture initially hit the live-system guard;
it now uses the documented opt-in for real signals to its own spawned tree,
with all cleanup assertions retained, and passes all 8 launcher/lifecycle cases.

TUI source regressions: **10 files, 144 passed**, exit 0. Coverage includes
phone composer widths, input wrapping/cursor, status/grid, model picker, terminal
setup, clipboard failure/fallback and URL opening. This is not packaged PTY or
Android keyboard/rotation evidence. Eight source skips are Docker (2), unavailable
host libpython (1), other-host staging (2), macOS bind (1), Windows native env (2).
They are not passed Android coverage. Full repository suite was not run.

Final auditor: **19 passed**, including a reproduced malformed-tar CLI traceback
converted to an actionable rejection. Final safe acceptance/bundle: **12 passed**.
APT signer/tamper: **14 passed**; new platform/filtered-child/plugin/env suite:
**21 passed, 2 Windows skips**; existing MCP safe-env subset: **5 passed**.
These overlap the 696-case total and must not be added to it. **44 regression
cases added**; existing assembly assertions and three wire fixtures strengthened.
Raw logs use `.build/termux/qualification/pre-device-*.log`. No check was disabled
or production gate bypassed. **NO KNOWN PRE-DEVICE IMPLEMENTATION BLOCKERS.**

## Migration, state and failure evidence

The observed `hermes-assets.nousresearch.com/releases/termux/stable` 404 source
is documented with the exact recursive grep command. Read-only detection reports
source filenames, never source URL content. Operators remove only the identified
source entry/file; remove its identified key only if no remaining source uses it.
No arbitrary APT source edits or automatic cleanup. Same `hermes-agent` identity
means replacement by version/origin selection, not dpkg coexistence. Foreign
launchers are refused; manual/source installs may shadow PATH. Existing profile
state is reused when selected; isolated acceptance precedes private-state reuse.

[End-user documentation](docs/termux.md) defines environment, package/user/cache/
temporary ownership and purge preservation. Diagnostic collection does not read
.env, credentials, full config, conversations or application logs. It reports
allowlisted metadata, runtime facts/paths and check statuses. Add only manually
reviewed error excerpts. No real provider credentials or paid turns were used.

## Outstanding environmental evidence

No production artifact exists. Static audit, Bionic runtime, installed validation,
component inventory and real size measurements must run on the exact candidate.
The actual N→N+1 signed upgrade requires two genuine packages and a verified
BLHermes-owned signing/feed environment. Test keys do not establish a public
identity. Independent fingerprint publication, atomic snapshots, immutable pool
and rollback requirements are documented for operators; no public URL is invented.

All twenty rows of [the device worksheet](docs/termux-device-acceptance.md) remain
pending. The offline driver reduces manual machine checks; it cannot prove real
streaming/provider auth, phone input/lifecycle, gateway messaging authorization,
optional permissions or persisted-state usability after real package changes.
API 24 is a build target, not the empirically supported Android minimum.

## Security and target limitations

No approval, profile/credential scoping, gateway auth or OS boundary was weakened.
Archive changes are ordinary release-input hardening under SECURITY.md §3.2;
no new §3.1 finding or security certification is claimed. Plugins/MCP retain the
user's authority. Base operation requires no root/Magisk/ADB/shared storage or
Termux:API. Target is standard com.termux aarch64/cp314; no PRoot runtime required.
Android suspension can delay/kill scheduler or gateway work. Electron/local
Chromium/Docker/nemo-relay/native clipboard/image/audio integrations remain
unqualified. Rolling build compiler packages preclude bit-identical reproducibility.

## Exact continuation

Use the final committed checkout on a native aarch64 Linux/glibc host with
working `docker info` and the tools/pinned PM environment in
[scripts/termux/README.md](scripts/termux/README.md). Run the canonical build above.
Retain deb, audit JSON, release JSON and complete container logs. Only after
production audit/Bionic/installed gates pass classify READY FOR DEVICE ACCEPTANCE.
Then run the safe driver and manual worksheet on the exact archive hash.
TERMUX RELEASE ACCEPTED is forbidden until real Android acceptance succeeds.
