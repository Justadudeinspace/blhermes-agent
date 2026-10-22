# BLHermes Termux release handoff

## 1. Release status

**BLOCKED — 2026-10-22.** No release `.deb` was produced in this session.
No clean Android installation, provider call, or real-device acceptance took
place. The existing broken/unsupported warning remains. Do not publish the
current work as an accepted Termux distribution.

This is an implementation and host-contract validation pass on top of
`23a035474c5f` and `BLHERMES_BASELINE.md`, not a repeated general audit.

## 2. Supported target

Candidate target, pending acceptance:

- Android/Bionic, ordinary unrooted Termux application-private storage.
- aarch64 / arm64-v8a only; Python wheel tag `android_24_arm64_v8a`, ABI cp314.
- Standard `com.termux` application ID and `/data/data/com.termux/files/usr`
  prefix. No PRoot requirement, ADB, Magisk, system-partition changes or root.
- Standard maintained Termux distribution from its official distribution
  channels. The exact tested Termux version, Android version and effective
  minimum Android version **remain unverified**. API 24 is a wheel target,
  not proof that every bundled runtime supports Android 7.
- Debian `.deb`, architecture `aarch64`, package `hermes-agent`, delivered
  through a signed APT repository. The public command remains `hermes`.

## 3. Implementation changes

### Build and artifact guards

Extended `scripts/termux/build.py` with `--prepare`; this reuses the existing
PM stagers, runtime-library stager and Bionic wheel builder before the existing
TUI/assembly sequence. Preparation checks host architecture/platform, required
tools, Docker access and tracked source cleanliness before downloading. Tool
staging and native compilation run sequentially. Subprocess deadlines diagnose
hung preparation steps. Existing CI can still consume its prepared payload.

Added `scripts/termux/audit_deb.py`, run automatically after assembly and before
the installed container gate. It inspects the actual archive: metadata/version,
fixed-prefix paths, link destinations, special files, setuid/setgid bits,
required layout, executable modes/shebangs, ELF64/AArch64, Android interpreter,
glibc version linkage, search paths and bundled SONAME inventory. It never
executes package code. JSON records SHA256 and sizes. Release artifact collection
now includes that report. This inventory check does not replace dynamic linking
or native imports on Bionic.

Both shell build paths now reject unavailable Docker daemons early. The
assembly path also requires `readelf` before doing work. Existing fail-closed
wheel-cache, offline completeness and native-import gates remain.

### Installed runtime and lifecycle

Added `runtime_probe.py`, invoked by the canonical installed validator. It
requires Android Python, checks package-local prefixes/site-packages, trust
store availability, ctypes, Unicode/temp files, SQLite persistence across an
interpreter restart, subprocesses, threads, asyncio, spawn multiprocessing and
signal delivery. It explicitly reports no network/provider test.

The validator additionally checks top-level help, gateway/MCP imports, skill
and plugin-manifest discovery, and real setup screens under both 120-column
and 40-column PTYs. Discovery is not activation; imports are not integration
acceptance. Installed checks still use disposable private state and no keys.

`check_deb.sh` now exercises removal, purge, preserved state outside the package,
and subsequent reinstall in the disposable container. Existing signed APT
upgrade tests preserve a sentinel and optionally consume a previous `.deb`.
Those container lifecycle steps could not run here.
Both package and APT smoke scripts invoke the validator with `-B`, keeping
the acceptance harness from creating unowned bytecode inside dpkg's runtime.

### Documentation and CI

End-user docs retain the broken status and stop presenting upstream's signed
feed as this fork's distribution. Candidate instructions separate repository
identity, installation, first launch, state, updates, permissions, gateway and
uninstall. `scripts/termux/README.md` contains operator/build instructions.
Host packaging CI includes the archive inspector and build-driver contracts.
No core tools, provider/plugin architecture, approval rules, security boundary
or dependency pins were changed.

## 4. Root causes found

Established evidence:

1. This host has **no Docker executable**. Both the wheelhouse entry point and
   the new complete build entry point stop at `missing tool: docker` before
   writing package output. This is a build-environment blocker, not evidence of
   a particular Android runtime defect.
2. The previous assembly path had no whole-archive host ELF/inventory gate.
   Its import tests remain valuable but cannot inspect every packaged ELF.
   A real `.deb` fixture containing a host glibc executable is now rejected.
3. The English Termux instructions directed BLHermes users to a Nous-owned feed
   and key. The baseline explicitly established that these are upstream
   infrastructure. No verified fork-owned replacement is available here.
4. Preparation was split between stagers, wheel builder and assembler without
   a complete local invocation. `build.py --prepare` now sequences those same
   implementations; no parallel installer was added.

The original upstream “Termux is broken” failure still has no reproduced crash
on the candidate package. This pass does **not** attribute it to any speculative
ABI, provider, permission or TUI issue. The source already records an earlier
ctypes/libffi packaging failure in `stage_runtime_libs.py`; that is historical
evidence, not a new device reproduction in this session.

## 5. Package build

On a native aarch64 Linux/glibc host with working Docker and the PM-provisioned
host toolchain, commit the reviewed implementation, then run:

```sh
python3 scripts/termux/build.py --prepare --repo . \
  --commit "$(git rev-parse HEAD)" \
  --payload .build/termux/payload --out .build/termux/deb
```

For immutable published tags substitute `--tag vX.Y.Z` for `--commit SHA`.
See `scripts/termux/README.md` for prerequisites and cache boundaries. The
builder's rolling apt toolchain prevents a claim of bit-for-bit reproducibility;
record its resolved image digest and compiler/package versions with the build.

## 6. Artifacts and size

**No release artifacts produced.** Release `.deb`, installed allocation,
Python contribution, Node contribution, native-library contribution and major
dependency totals are **unmeasured**, not zero. Synthetic test archives are
temporary test fixtures and must never be distributed as BLHermes.

On a successful build, preserve `hermes-agent_VERSION_aarch64.deb` and
`hermes-agent_VERSION_aarch64.deb.audit.json`. Independently rerun:

```sh
python3 scripts/termux/audit_deb.py "$deb" --version "$version" --report inspection.json
dpkg-deb -f "$deb" Package Version Architecture Installed-Size
sha256sum "$deb"
```

The report separates compressed size, logical payload bytes, component totals
(including Python, Node and runtime libraries) and largest files. Inspect
site-packages contributors in the extracted *trusted build artifact* if finer
dependency totals are needed. No size/reliability tradeoff was made without an
artifact measurement.

## 7. Automated validation

Validation uses the existing disposable PM-built Python/test environments from
the baseline, with isolated state. At most two background jobs; test runner
uses one worker. No raw pip/uv mutation.

Initial focused command:

```sh
scripts/run_tests.sh -j 1 --file-retries 0 --file-timeout 180 \
  tests/scripts/test_termux_artifact_audit.py \
  tests/scripts/test_termux_build_driver.py \
  tests/scripts/test_termux_update_refusal.py
```

Result: 3 files, **31 passed**, exit 0. Subsequent strengthened-code validation
is recorded below before handoff; this initial receipt alone does not certify
the final implementation.

Build attempts:

```sh
bash scripts/termux/termux_build.sh --repo . --commit "$(git rev-parse HEAD)" \
  --out .build/termux/payload
python3 scripts/termux/build.py --prepare --repo . --commit "$(git rev-parse HEAD)" \
  --payload .build/termux/payload --out .build/termux/deb
```

Both exit 1: Docker missing. No emulated or installed-product test occurred.

## 8. Installed validator

On the clean device **after installing the accepted candidate package**:

```sh
export PREFIX=/data/data/com.termux/files/usr
root="$PREFIX/lib/hermes-agent"
PYTHONPATH="$root/app" \
LD_LIBRARY_PATH="$root/tools/python$PREFIX/lib:$root/tools/node$PREFIX/lib:$root/tools/ffmpeg$PREFIX/lib:$root/runtime-libs/lib:$PREFIX/lib" \
  "$root/venv/bin/python" -B "$root/app/scripts/termux/validate_installed.py"
```

Coverage: disposable state, CLI version/help, ACP check, Android runtime
contracts, backend/gateway/MCP imports, every recorded native wheel import,
skill/plugin-manifest discovery, Node/npm versions, ripgrep, FFmpeg conversion,
PM runtime-tool verification, updater refusal, and two PTY setup-screen widths.
Exit 0 and `INSTALLED_BUNDLE_VALIDATION_OK` are required. This command is offline;
it does not activate a plugin/MCP service, start a gateway, call a provider or
verify touch/keyboard rendering on Android.

## 9. Real-device acceptance procedure

Record device model, Android/API level, Termux app source/version, package
version, source commit, SHA256, commands, exit codes and redacted logs. Do not
paste keys, conversation databases or unredacted configuration into reports.
Every test below is **pending**. A skipped critical test blocks acceptance.

### A — clean signed installation

Use a fresh standard aarch64 Termux app. Maintainer must first publish and
independently communicate the BLHermes URL and signing fingerprint. These are
required release inputs, not values to guess from upstream.

```sh
pkg update
pkg install curl gnupg ca-certificates
read -r -p 'Published BLHermes repository URL: ' repo_url
read -r -p 'Published primary key fingerprint (no spaces): ' expected_fingerprint
mkdir -p "$PREFIX/etc/apt/keyrings"
curl -fSL "$repo_url/key.asc" -o "$PREFIX/etc/apt/keyrings/blhermes.asc"
actual_fingerprint=$(gpg --show-keys --with-colons "$PREFIX/etc/apt/keyrings/blhermes.asc" | awk -F: '$1=="fpr" {print $10; exit}')
test "$actual_fingerprint" = "$expected_fingerprint" || { echo 'STOP: fingerprint mismatch'; exit 1; }
printf 'deb [signed-by=%s/etc/apt/keyrings/blhermes.asc] %s hermes-stable main\n' \
  "$PREFIX" "$repo_url" > "$PREFIX/etc/apt/sources.list.d/blhermes.list"
pkg update
pkg install hermes-agent
dpkg-query -W hermes-agent
hermes --version
hermes --help
```

Stop on any failure. Run the validator command in section 8 and save its output.
Do not disable APT signatures. Candidate direct-dpkg installation may diagnose
an artifact but does not satisfy clean signed-source acceptance.

### B — first boot and TUI

Run `hermes`, complete setup with your provider, then run `hermes --tui`.
Verify portrait 40-column rendering, keyboard entry, long output/scrolling,
Unicode, history, rotation/resizing, cancellation with Ctrl+C, normal exit and
Ctrl+D behavior. Background/resume the Termux app and verify the UI recovers.
Record clipboard/optional feature limitations separately.

### C — optional authenticated provider smoke (required for release acceptance)

Use `hermes setup` for your own credentials. This test incurs the provider's
normal charges. No maintainer credentials are required by automated validation.

```sh
hermes chat --oneshot -q 'Reply with the single word READY.'
```

Verify an actual successful provider response, then send an interactive turn
in the TUI and verify streaming, cancellation and recovery. An exit status or
mocked response alone is insufficient. Do not pass keys on the command line.

### D/E — tool call and persistence

```sh
mkdir -p "$HOME/blhermes-acceptance"
cd "$HOME/blhermes-acceptance"
hermes
```

Ask the agent to create `proof.txt` containing `termux acceptance`, read it
back and execute `pwd` through its terminal tool. Observe approvals and actual
tool results. Exit and check `cat proof.txt`. Restart `hermes`; verify configured
provider/model, history and expected session state. Resume the test conversation.
Repeat a run with a separate explicit `HERMES_HOME` and confirm profile isolation.

### F/G/H — skills, plugin and MCP

Run `hermes skills list` and use a bundled skill compatible with Android and
your provider. Record the skill name and visible behavior. Run
`hermes plugins list`; review, enable and exercise one compatible plugin using
the normal CLI workflow, then restart and confirm its state. Record its version
and any dependencies; discovery alone is not a pass.

Configure one reviewed, pinned, harmless MCP server using the normal MCP
configuration workflow. A loopback-only read-only service is preferable.
Verify discovery, a real tool result, timeout/cancellation, and child cleanup
on exit. Record command/version or URL and bind address. Do not use an arbitrary
unpinned `npx` package as a release test. The concrete plugin/MCP fixtures still
need selection and successful device receipts; this is a release blocker.

### I — foreground gateway

Configure an adapter and explicit sender allowlist through normal setup. Run
`hermes gateway run`, exchange an authorized test message, reject an unauthorized
sender and verify any local listener is loopback-only. Ctrl+C; check logs and
confirm child/listener cleanup before restarting. Do not automatically expose
a port or rely on Android background durability.

### J/K — upgrade and reinstall

The maintainer must publish two sequential candidate versions to the same test
signed suite. With version N configured and used, record permissions and
private local hashes/backups of config, credentials and state. Then:

```sh
pkg update
pkg upgrade hermes-agent
dpkg-query -W hermes-agent
hermes --version
apt reinstall hermes-agent
```

Verify N+1 actually replaced N, setup was retained, sessions resume and files,
skills and plugins persist. State databases may legitimately change; verify
contents and migration behavior rather than demanding identical database hashes.
Run section 8 again and complete another turn after reinstall.

### L — remove, purge and reinstall

Back up state locally first; it contains secrets. Close BLHermes/gateway, then:

```sh
pkg uninstall hermes-agent
test ! -e "$PREFIX/lib/hermes-agent"
test ! -L "$PREFIX/bin/hermes"
```

Verify configured state and `proof.txt` survived. `apt purge hermes-agent` must
also preserve private profile data. Reinstall from the signed feed and confirm
configuration/history remain usable. Package removal is not credential erasure.

### M — failure UX

Temporarily disable networking: verify provider timeout/cancellation is bounded
and actionable; restore networking and recover. In a disposable profile test an
invalid API key, then restore the valid configuration. Attempt an unsupported
optional integration and record its message. Attempt an explicitly requested
shared-storage operation before granting storage permission; require a clear
permission/action message. Base startup must work without shared storage or
Termux:API. Tracebacks, hidden repairs or manual pip fixes fail acceptance.

## 10. Known limitations

- No real release artifact/native dependency inventory, runtime or device UX
  receipt exists for this implementation yet.
- No fork-owned verified public signed feed/signing identity has been supplied.
- Exact minimum Android version and supported Termux app version are unverified.
- Arbitrary native plugin/MCP dependencies are not certified for Bionic/cp314.
- Existing exclusions: nemo-relay exporter, Electron, local Chromium/desktop
  computer use, local Docker and phone-native clipboard/microphone adapters.
- Android can suspend/kill Termux; no ordinary Linux daemon durability is promised.
- Compiler provisioning still uses rolling Termux apt, so byte reproducibility
  is not established.

## 11. Security notes

Base operation uses private Termux storage without shared-storage permissions.
User secrets and state are outside dpkg ownership. Shared-storage access is
optional and intentionally broad once granted. Plugins and MCP subprocesses
inherit the Termux user's authority; a manifest or skill is not permission to
trust code. Retain existing approval, credential, environment-scrubbing and
gateway allowlist protections. Never bypass TLS or repository signatures.
The archive inspector is a packaging check, not a security certification.

## 12. Update and uninstall behavior

APT owns runtime replacement: `pkg update` then `pkg upgrade hermes-agent`.
`hermes update` refuses APT modifications; commit artifacts also refuse channel
updates. Existing state migrations must run against preserved profile state
and still require N→N+1 device acceptance. No migration policy was changed.

Maintainer hooks create only declared command symlinks, refuse foreign launchers,
preserve links during upgrade, and remove owned links on removal. Neither
removal nor purge deletes profile data. Reinstall reuses state. No background
service is installed or automatically exposed. Stop running sessions before
package replacement/removal for acceptance.

## 13. Remaining release blockers

1. Run the committed implementation on a Docker-capable native aarch64 build
   host; produce the complete `.deb`, audit report, component sizes and successful
   fresh Bionic container install/lifecycle receipts.
2. Audit the resolved wheel/dependency inventory from that artifact; close any
   ELF, missing SONAME, import or stdlib failures. No complete A–E dependency
   categorization can be asserted without the resolved artifact graph.
3. Provision and verify fork-owned signing/feed infrastructure; validate signed
   APT installation and upgrade with a recorded previous version.
4. Complete all critical real-device tests A–M, including first boot/TUI, a paid
   authenticated turn, tools, concrete skill/plugin/MCP fixtures, gateway,
   restart, update/remove and failure UX. Record effective OS/app minimums.
5. Resolve any final host validation failures recorded below. No passing host
   lane waives items 1–4 or authorizes removal of the broken warning.

## 14. Next action

Review and commit this implementation, move it to a native aarch64 Linux host
with working Docker, and run the exact `build.py --prepare` command in section 5.
Inspect the emitted archive/report before provisioning the signed device-test
feed. Stop after a validated artifact is ready for clean real-device acceptance;
do not claim support until the device receipts pass.

### Final host receipts

The expanded regression invocation used the same one-worker, zero-retry,
180-second per-file options and these eleven files:

```sh
scripts/run_tests.sh -j 1 --file-retries 0 --file-timeout 180 \
  tests/scripts/test_termux_artifact_audit.py \
  tests/scripts/test_termux_build_driver.py \
  tests/scripts/test_termux_update_refusal.py \
  tests/scripts/test_termux_launchers.py \
  tests/scripts/test_termux_agent_assembly.py \
  tests/scripts/test_termux_runtime_libs.py \
  tests/scripts/test_stage_apt_repo.py \
  tests/scripts/test_termux_build_wheels.py \
  tests/scripts/test_termux_python_linkage.py \
  tests/scripts/test_termux_retag_wheel.py \
  tests/scripts/test_termux_assembly_permissions.py
```

Result: **63 passed, 3 failed, 3 skipped**, exit 1, 233.3 seconds. All three
failures were real signed-repository verification tests unable to find `gpgv`
on the deliberately restricted test PATH. No signing code was changed. The
existing Termux GnuPG verifier was explicitly checked (`gpgv` 2.5.24), and its
directory appended after the PM/Debian toolchain for this rerun:

```sh
export PATH="$PATH:/data/data/com.termux/files/usr/bin"
scripts/run_tests.sh -j 1 --file-retries 0 --file-timeout 180 \
  tests/scripts/test_stage_apt_repo.py \
  tests/scripts/test_termux_build_driver.py \
  tests/scripts/test_termux_artifact_audit.py
```

Result: **40 passed, 0 failed**, exit 0, 76.8 seconds, including independent
signature verification and rejection of tampered repository metadata. This is
a mixed-host signing-tool receipt, not installed BLHermes Android acceptance.
Overlapping reruns must not be summed. The three broad-run skips remain skips,
not passed ownership/linker coverage on an unexercised host.

The first health run correctly rejected missing subprocess deadlines; those
were fixed. The first footguns run rejected a BOM-intolerant read and POSIX-only
signal references; the probe now reads UTF-8 with BOM support and tests SIGINT
delivery. No guard was waived. The final guard results are recorded below.

The final archive-size reporting change was retested with
`scripts/run_tests.sh -j 1 --file-retries 0 --file-timeout 180 tests/scripts/test_termux_artifact_audit.py`:
**5 passed**, exit 0, 13.3 seconds. These use actual synthetic `.deb` archives,
not a runnable BLHermes package. Final report fields also include native-library
bytes and the largest site-packages directories.

All **12 blocking guard lanes passed**, invoked individually with
`python scripts/check --only "$termux_check" --base HEAD` for footguns,
shebangs, no-tmp, config-writers, os-marker-fakes, agents-md, case-collisions,
lazy-deps, profile-archives, blob-size, ruff and health. This base is the committed
baseline for this implementation pass, not an assertion about all historical
upstream divergence. The final Ruff/health recheck passed (six Python files,
zero blocking and zero advisory health findings). Shell syntax checks of
`build_deb.sh`, `check_deb.sh`, `check_apt.sh` and `termux_build.sh`, and
`git diff --check`, passed.

The new host-refusal test initially asserted an empty pytest temporary root,
which already contained the suite's isolated state fixture. It now uses a fresh
dedicated prefix and verifies no probe state is created there. This correction
does not change the runtime's refusal behavior.
Final command:
`scripts/run_tests.sh -j 1 --file-retries 0 --file-timeout 180 tests/scripts/test_termux_runtime_probe.py`:
**1 passed**, exit 0, 7.9 seconds. It confirms the Linux interpreter cannot emit
an Android acceptance receipt or create probe state.
