# BLHermes Termux release qualification

## 1. Release status

**BLOCKED** — 2026-10-22 resumed release-candidate pass.

No real production `.deb` was built. Artifact audit, Bionic runtime, installed
validation and real Android acceptance are pending. Production installation is
currently unsupported; no current candidate runtime defect was reproduced.
The missing build environment is sufficient to block release qualification.
[BLHERMES_BASELINE.md](BLHERMES_BASELINE.md) remains a historical receipt.

## 2. Source commit and recovered state

Inspected source: `dceb35b84f8289799a297a429b452d88af0ffd46` on `main`.
The final qualification source is the commit containing this document;
no package is attributed to that commit. Build the final committed checkout.

Initial `git status --short` was **not clean**: modified `README.md`,
`README.es.md`, `README.ur-pk.md`, `README.zh-CN.md`, and untracked `docs/`
(containing only `termux.md`). These were recovered interrupted-pass edits,
reviewed and retained. No runtime/source edits were present. Initial history:

```text
dceb35b84f Add files via upload
feb01f4675 Delete assets/banner.png
ade35f0bb6 Add banner.png
d37bd2161e Delete assets/banner.png
efb02db784 Add banner.png
0fe6747672 Delete assets/banner.png
88a3799487 Add banner.png
f7a59019fc Delete assets/banner.png
168931886a Improve Termux artifact validation and document release gates
23a035474c chore: establish BLHermes branding and baseline audit
```

`git ls-remote origin refs/heads/main` matched the inspected HEAD before edits.
The interrupted `check.log` was empty; `termux-tests.log` ended after two passing
files without an exit receipt. Neither is counted as completed qualification.

Verified all seven required scripts exist: `build.py` orchestrates preparation,
TUI and assembly; `audit_deb.py` inspects the actual archive without execution;
`runtime_probe.py` requires packaged Android Python; `validate_installed.py`
exercises installed commands/imports/PTY; `termux_build.sh` builds Bionic wheels;
`build_deb.sh` assembles, audits and installs in a fresh pinned container;
`stage_apt_repo.py` stages and signs repository metadata. All contract test paths
in `.github/workflows/termux-verify.yml` and `tests/home_io_guard.py` exist.

Discrepancies found before new edits: the previous handoff said README material
had stopped directing users to upstream Termux docs, but HEAD still did so in all
four READMEs. Its “broken” language had no current candidate crash receipt.
The prior handoff is superseded by this pass's evidence, not assumed correct.

## 3. Build environment

Actual host: Debian GNU/Linux 13.7, glibc 2.41, aarch64, under PRoot on the
`6.17.0-PRoot-Distro` Android kernel. Approximately 31 GiB free at inspection.
System Python was 3.13.5; reused PM host Python is 3.14.7, Node v26.7.0,
Git 2.47.3. Existing isolated PM test/lint environments were reused without
raw pip/uv mutation. Isolated operator state is under `.build/termux/qualification`.

`bash`, Git, curl, Python, Node, dpkg-deb, jq, readelf and gpg are available.
`gpgv` resolves to the existing Termux executable; signing tests therefore
constitute mixed-host contracts. Host `patchelf` was initially absent. Debian trixie arm64 package
`patchelf=0.18.0-1.4` was downloaded with APT and extracted into disposable
`.build/termux/qualification/host-tools` (no system installation). The final
regression PATH includes its `usr/bin`; the real shared-libpython contract still
skips because the PM interpreter reports `/install/lib/libpython3.14.so`,
which is absent. The wheel RECORD-rewrite linkage test runs. PyPI HTTPS HEAD returned
HTTP 200; that alone does not qualify every pinned runtime download.

**Docker executable: absent. Docker version/daemon: unavailable.** Neither
`/var/run/docker.sock` nor `/run/docker.sock` exists. No external build host was
provided. Installing a client alone would not provide the required native
Docker daemon in this PRoot session; no root, device modification or unverified
emulation was attempted. The supported continuation requires a native aarch64
Linux/glibc host with working Docker, PM Python/Node and documented host tools.

## 4. Build command

The actual CLI was inspected (`build.py --help` and source). Canonical command:

```sh
python3 scripts/termux/build.py --prepare --repo . \
  --commit "$(git rev-parse HEAD)" \
  --payload .build/termux/payload --out .build/termux/deb
```

`--prepare` checks Linux/arm64, required tools, Docker access and tracked source
cleanliness before staging. Commit the reviewed tree first. No source changes
are used to bypass build or artifact gates.

## 5. Build result

Canonical command above exited **1** with `missing build tool: docker`.
Full output: `.build/termux/qualification/build-resumed.log`. No payload or
production output directory was created. This run selected the inspected source
commit; dirty documentation was never mixed into a package because preparation
stopped at its prerequisite gate.

Classification: **A — environmental**. No production compiler, wheel, linker,
Node build or package stage ran. No downstream failure is inferred.

## 6. Artifacts

**No production artifacts produced.** Filename, version, SHA-256, compressed
size, installed size and build timestamp: **unavailable**, not zero.
No machine-readable candidate release summary was emitted because no candidate
exists. Synthetic test archives are not release candidates.

Local raw logs are retained under `.build/termux/qualification/` (ignored build
output, not a published artifact). Commands and final results are recorded below
so the tracked handoff remains usable if temporary environments disappear.

## 7. Static artifact audit

**NOT RUN on a production package**. Auditor contract tests use synthetic `.deb`
fixtures, including rejection of host ELF/glibc payloads. They cannot establish
that an actual candidate has no glibc contamination. On a real build preserve
`hermes-agent_VERSION_aarch64.deb.audit.json` and independently run:

```sh
python3 scripts/termux/audit_deb.py "$deb" --version "$version" --report "$deb.audit.json"
dpkg-deb -f "$deb" Package Version Architecture Installed-Size
sha256sum "$deb"
```

Any unacceptable glibc linkage, layout, mode, interpreter or missing SONAME
finding blocks the candidate. No exception or whitelist was added.

## 8. Bionic runtime results

**NOT RUN**: no packaged interpreter or Bionic container is available. Host
probe-refusal coverage is distinct from Android acceptance. The real probe
checks Android identity, package-local prefix/site-packages, TLS CA discovery,
ctypes, SQLite across restart, Unicode/temp files, threading, asyncio, subprocess,
spawn multiprocessing and signals. Installed validation also imports ssl,
sqlite3, bz2, lzma, zlib, hashlib and readline. Record actual `sys.path`,
`sys.prefix`, API level, state and temp directory when the package runs.

## 9. Installed validator and TUI results

**NOT RUN against an installed production package.** The canonical validator
covers version/help/chat help, ACP, backend/gateway/MCP imports, native wheel
imports, skill/plugin discovery, Node/npm, ripgrep, FFmpeg conversion, PM tools,
updater refusal and setup-screen PTYs at 120 and 40 columns. It does not prove
an authenticated provider turn, live gateway or integration activation.
The manual worksheet additionally requires 80 columns, phone-like height,
resize, keyboard/input, cancellation and process cleanup.

Host validation commands (PM environment described in section 3; one worker,
sequential guard lanes to control concurrency):

```sh
for lane in footguns shebangs no-tmp config-writers os-marker-fakes agents-md case-collisions lazy-deps profile-archives blob-size ruff health; do
  python scripts/check --only "$lane" --base dceb35b84f8289799a297a429b452d88af0ffd46 || exit $?
done
scripts/run_tests.sh -j 1 --file-retries 0 --file-timeout 180 \
  tests/scripts/test_termux*.py tests/scripts/test_archive_inputs.py \
  tests/scripts/test_stage_apt_repo.py tests/pm/test_pm_bionic.py \
  tests/pm/test_stage_only.py tests/pm/test_deb_safety.py tests/pm/test_termux_libs.py \
  tests/ci/test_termux_input_archive.py tests/scripts/test_run_tests_shell.py \
  tests/scripts/install/test_install_sh_termux_refusal.py \
  tests/hermes_cli/test_termux_gateway_launch.py
npm run test --workspace ui-tui -- --maxWorkers=1 --no-file-parallelism \
  src/__tests__/termuxComposerLayout.test.ts src/__tests__/textInputWrap.test.ts \
  src/__tests__/cursorDriftRegression.test.ts src/__tests__/statusRule.test.ts \
  src/__tests__/appChromeStatusRule.test.tsx src/__tests__/widgetGrid.test.ts
python -m compileall -q scripts/termux
for script in scripts/termux/*.sh; do bash -n "$script" || exit $?; done
git diff --check
```

Final guard: **12/12 lanes passed**, exit 0, including Ruff and health. Health
reported no measured files changed (the executable fix is shell, not Python).
Final Termux regression: **24 files, 170 passed, 0 failed, 5 skipped**, exit 0,
453.8 seconds.
The five skips are two Docker ownership cases, one shared-libpython case and
two staging cases requiring x86_64 Linux / Windows. They are not passed native
linker, Docker or other-host coverage. The final run includes all fourteen
signed APT staging tests and five synthetic archive-auditor tests.
TUI: **6 files, 79 passed**, exit 0, 24.62 seconds. This is a Linux source
layout/input/status regression, not packaged PTY/device validation.
Python/shell syntax and diff whitespace: pass. An ad hoc local-link and shell
snippet check passed **17 local links / 11 shell blocks** across the new guides,
handoff, operator guide and README Termux links; no external-link/site build
claim is made. Full repository suite was not run.

Initial broader run: **24 files, 169 passed, 1 failed, 5 skipped**, exit 1,
433.6 seconds. The sole failure was source identity versus Docker preflight
ordering, reproduced narrowly with the canonical runner (**1 failed**, exit 1),
then fixed and rerun (**1 passed**, exit 0). Same runner options, selecting only
`tests/scripts/test_termux_commit_identity.py`. Existing contract coverage was
retained; neither a suppression nor a new duplicate test was needed.
Initial twelve guard lanes passed. Logs: `check-resumed.log`,
`termux-tests-resumed.log`, `identity-before.log`, `identity-after.log`,
`check-final.log`, `termux-tests-final.log`, `tui-resumed.log` under the local
qualification directory. Overlapping reruns are not added together.

## 10. Package size breakdown

All actual size measurements are **PENDING**: compressed `.deb`, Installed-Size,
Python, Node, FFmpeg, uv, ripgrep, site-packages, native runtime libraries,
TUI/static assets and top twenty files. No artifact was available to inspect
for duplicate runtimes/libraries, caches, debug files or source trees. No size
optimization was made without measurements. Logical payload bytes in the audit
must be distinguished from dpkg's allocated Installed-Size.

## 11. Package lifecycle results

Actual install/remove/purge/reinstall: **BLOCKED** by environment/artifact.
Existing `check_deb.sh` checks removal of owned runtime/launchers, preserved
external sentinel, purge and reinstall in its disposable container. That is
not yet a representative configured profile usability receipt. The device
worksheet tests real isolated configuration/conversation state as well.
Actual N→N+1 upgrade: **PENDING**, no two genuine candidates available.
Same-version reinstall and synthetic version-order tests do not satisfy it.

## 12. APT/signing status

**PUBLIC APT DISTRIBUTION: NOT PROVISIONED.** No BLHermes public URL, signing
fingerprint or release service was invented or published. Upstream Nous's feed
and identity are not BLHermes infrastructure. Local/test signing contracts cover
metadata/checksums, signature verification and tamper rejection; see host results.
Real signed APT install/upgrade selection remains blocked pending actual versions,
a verified test signing identity and a supported container/device environment.
Existing release CI requires signing/R2 provisioning; an unprovisioned fork's
skipped native job is not acceptance.

## 13. Provider status

**REAL MODEL TURN: PENDING DEVICE ACCEPTANCE.** No real credential was used,
printed or committed. Installed provider configuration, missing/invalid key,
network failure, timeout, cancellation and streaming behavior are unqualified
for this candidate. Source/mock coverage cannot replace a packaged real turn.

## 14. Skills / plugins / MCP status

Installed infrastructure discovery/imports: **PENDING**. Live integration tests:
**PENDING**. Select reviewed, pinned Android-compatible fixtures before device
acceptance. Infrastructure compatibility never certifies all third-party skills,
plugins or MCP servers. Native dependencies must support Bionic/cp314.

## 15. Gateway status

Installed gateway import/start/listener/log/shutdown/process cleanup:
**PENDING**. Foreground operation only is intended; no fake systemd semantics,
automatic external bind or background durability promise. Adapter authentication
and explicit sender allowlists remain required. Android may suspend/kill Termux.

## 16. Documentation changes

English, Spanish, Urdu and Chinese README Termux notices now consistently state
release acceptance pending and production installation unsupported, with links
to repository-owned guidance and separation from the upstream distribution.
[End-user guide](docs/termux.md) covers status/target/install/launch/providers,
state, updates, optional permissions, gateway, integrations, removal and failures.
[Device acceptance worksheet](docs/termux-device-acceptance.md) gives twenty
pending tests with expected results and failure evidence. Operator README remains
technical and links these documents. The historical baseline was not rewritten.

## 17. Known limitations and target

Candidate: `hermes-agent`, command `hermes`, architecture `aarch64`, standard
unrooted `com.termux` prefix `/data/data/com.termux/files/usr`.
Wheel target `android_24_arm64_v8a`, ABI cp314. **Minimum supported Android and
Termux versions remain empirically unestablished**; API 24 is not acceptance of
Android 7. No PRoot requirement for end users. Desktop/Electron, local Chromium,
local Docker, nemo-relay exporter and native phone clipboard/microphone adapters
are not qualified. Rolling Termux compiler packages prevent a bit-for-bit
reproducibility claim even though runtime inputs/base image/graph are pinned.
Prior baseline full-suite/scratch/typecheck limitations are not resolved by this
focused pass; no broad repository or security certification is claimed.

## 18. Security notes

The only executable change moves the assembly Docker daemon probe after source
identity and input admission, still before output creation or payload mutation.
The previous pass added it before commit admission (`git log -p -S 'docker info'`
points to `168931886a`), breaking the existing invalid-commit refusal test.
That test reproduced red on the inspected source before the move; no tests or
checks were disabled. No application runtime, credential-path classification,
file/approval policy, sandbox mirror, YOLO boundary, plugin/MCP execution,
gateway authentication, webhook, remote backend, secret scrubbing or filesystem
mode was changed. No new trust-boundary claim is made. Base agent needs private
Termux storage only: no root, Magisk, ADB, shared storage or Termux:API requirement.
Plugin/MCP code retains the Termux user's authority. Existing protections and
`SECURITY.md` remain authoritative. Test keys are disposable, not a public identity.

Additional source security regression:

```sh
scripts/run_tests.sh -j 1 --file-retries 0 --file-timeout 180 \
  tests/agent/test_file_safety.py tests/agent/test_file_safety_write_credentials.py \
  tests/agent/test_file_safety_cross_profile.py tests/agent/test_file_safety_sandbox_mirror.py
```

**4 files, 29 passed, 0 failed, 0 skipped**, exit 0, 90.3 seconds. Log: `.build/termux/qualification/security-final.log`.
This exercises credential-path/write/profile/mirror behavior on Linux; it is
not Android acceptance or a new review of every gateway/plugin/MCP boundary.

## 19. Real-device tests still required

All twenty tests in [the worksheet](docs/termux-device-acceptance.md) are pending:
clean environment/install/validator, first boot, provider setup/streaming,
terminal/file tools, state, skill/plugin/MCP, gateway, restart, real upgrade,
reinstall/remove/purge, offline/invalid-key/optional-permission UX. Save device,
OS/app versions, commit, package hash and redacted results. A skipped critical
test blocks acceptance. Host Linux cannot issue a device acceptance receipt.

## 20. Public distribution blockers

1. Supported native aarch64 Docker build environment and real `.deb`.
2. Passing real archive audit, Bionic runtime, installed/lifecycle validation,
   component inventory and size evidence; emit the machine-readable release summary.
3. Real device qualification including actual streaming model turn, integrations,
   gateway and state behavior; empirically establish supported Android/Termux versions.
4. BLHermes-owned signing/feed infrastructure and meaningful signed N→N+1 acceptance.

## 21. Exact next action

Move the final committed checkout to a **native aarch64 Linux/glibc host with a
working Docker daemon**. Provision the pinned PM Python/Node environment using
CONTRIBUTING.md, isolated operator state and all tools in scripts/termux/README.md.
Confirm `docker info` succeeds and `git status --porcelain` is empty, then:

```sh
mkdir -p .build/termux
set -o pipefail
python3 scripts/termux/build.py --prepare --repo . \
  --commit "$(git rev-parse HEAD)" \
  --payload .build/termux/payload --out .build/termux/deb \
  2>&1 | tee .build/termux/production-build.log
```

Retain complete logs, resolved image digest/toolchain versions, archive/audit,
real component sizes and installed receipts. Only after every required container
gate passes change status to READY FOR DEVICE ACCEPTANCE and stop engineering
work for the real device worksheet. TERMUX RELEASE ACCEPTED requires actual
successful device acceptance; it is not permitted by this pass's evidence.
