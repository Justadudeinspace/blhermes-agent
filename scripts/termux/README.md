# Building the Termux distribution

This is operator documentation. The intended end-user distribution is a signed
APT package; public BLHermes APT distribution is not provisioned. End users
never build Python, wheels, or the frontend on their phone. Production support
remains pending the release gates in `BLHERMES_TERMUX_RELEASE.md`. See the
[end-user guide](../../docs/termux.md) for current installation status.

## Build

Use a native aarch64 Linux/glibc host with a working Docker daemon, enough disk
space for native build caches, and the checkout's PM-provisioned Python and Node
on PATH. Required host commands: bash, git, curl, python3 (3.11+), node, docker,
dpkg-deb, jq, readelf (binutils). No root or Docker is required on the phone.
Use isolated `HERMES_HOME` and `HERMES_RUNTIME_DIR` for the operator environment,
following the package-management developer guide. Commit the reviewed source
first: application code is archived from the selected commit, not dirty files.

One entry point stages the pinned runtimes, builds Bionic wheels, builds the
shared TUI, assembles the package, inspects the archive and runs the existing
offline installed validator in a fresh digest-pinned Bionic container:

```sh
python3 scripts/termux/build.py --prepare --repo . \
  --commit "$(git rev-parse HEAD)" \
  --payload .build/termux/payload --out .build/termux/deb
```

For a published immutable release tag, use `--tag vX.Y.Z` instead of `--commit`.
Commit artifacts deliberately have no self-update channel. Release CI retains
its staged/cache-aware phases and calls the same entry point without
`--prepare`. No second installer is introduced.

`payload/` holds staged tools, verified wheelhouse caches, and `.work/` evidence;
`deb/` holds the final `.deb` and `.deb.audit.json`. Reruns verify cached inputs
before reuse. Do not publish `.work`, wheel build environments or staging trees.
A failed build is not a release even if an intermediate `.deb` exists.

Builds pin runtime artifacts, Python graph, base container and wheel toolchain.
The builder's apt-installed compiler packages still come from the rolling
Termux repository. This is not a claim of bit-for-bit reproducible builds.
Record the builder image digest and toolchain versions with each acceptance.

## Host inspection

```sh
python3 scripts/termux/audit_deb.py .build/termux/deb/hermes-agent_VERSION_aarch64.deb \
  --version VERSION --report .build/termux/deb/inspection.json
```

The inspector streams the archive without extracting or executing its payload.
It checks metadata, fixed-prefix layout, paths, links, executable modes,
launcher shebangs, ELF64/AArch64, Android interpreter, glibc linkage, RPATH and
SONAME inventory. It records SHA256, compressed bytes, payload bytes, Python,
Node, runtime-library and other component totals, and the twenty largest files.
Payload bytes are logical file sizes; `Installed-Size` is filesystem allocation
reported by the assembler. SONAME inventory is not dynamic-loader resolution;
the container import gate and device validator remain required.

## Publish and accept

`scripts/termux/stage_apt_repo.py` builds signed `dists/` and `pool/` layouts.
It fails when signing is unavailable. Existing `check_apt.sh` verifies signed
APT install and, with a prior package, upgrade/state preservation in a container.
Provision a BLHermes-owned URL, key, release-signing environment and runner;
upstream Nous feeds are not this fork's release service. Publish no support
claim until the real-device procedure passes on the exact archive hash.

The twenty-test [device acceptance worksheet](../../docs/termux-device-acceptance.md)
and `BLHERMES_TERMUX_RELEASE.md` record the manual procedure and outstanding
gates. Container results never count as Android device UX or authenticated
model acceptance.

## Pre-device receipts and publication contract

`device_acceptance.py --safe --output NEW.json` is the offline, non-destructive
machine driver. Run it with the packaged interpreter and library environment in
the device worksheet. It refuses host Linux as Android evidence, uses disposable
state and emits private facts/check statuses without reading app logs or secrets.
`diagnostics.py` supplies read-only stale upstream source detection. The
[end-user migration guide](../../docs/termux.md#migrating-an-existing-upstream-hermes-installation)
explains the same-package replacement and explicit source/key cleanup decision.

`release_manifest.py --commit FULL_SHA --output summary.json` emits schema v1
with unknown archive measurements set to JSON null and unexecuted gates pending.
With `--deb`, it reruns the actual auditor and fills archive identity/hash/size
and Installed-Size (KiB). The assembler adds `--container-validated` only after
its mandatory real Bionic/installed gate. Never use that flag for host tests.
`audit_filename` stays null unless a separately retained report is associated;
device/public-APT/minimum-Android status is never promoted by host assembly.
Every field required by the release ledger is emitted even for a blocked build.

The public layout is a separately provisioned HTTPS root with `key.asc`,
`pool/<first-character>/...deb`, and `dists/hermes-stable/` (optional
`hermes-canary`) containing the existing signed Release/InRelease, index and
by-hash objects. No URL is assigned by this repository. Operators must publish
the signing fingerprint through an independent trusted channel, protect the
signing key, stage in an unpublished directory, verify both signatures/checksums,
then atomically switch the served snapshot. Retain immutable pool/by-hash objects
for clients using the previous signed index. Roll back a bad publication by
restoring a complete signed snapshot; clients with a newer version need an
explicit reviewed downgrade or a higher-version repair package. Never replace
bytes behind an existing version/filename. Canary promotion requires the same
acceptance gates as stable. Untrusted PRs must never access publishing secrets.

The wheel export uses the declared `termux` baseline (MCP, cron and ACP), not
desktop `all` and not the best-effort `termux-all` profile. The frozen exported
graph is classified by Android markers; none-any wheels are fetched, applicable
native distributions are built against the staged Bionic Python, excluded
markers remain excluded, and the documented nemo-relay miss stays unsupported.
`resolved.txt`, `build_set.txt`, `index.json` and SHA256SUMS retain the exact graph,
classification and hashes. The installed validator imports every build-set
entry and runs a real read-only local MCP fixture. Optional integrations still
need explicit selection and Android-compatible dependencies.

The pinned rg is a static AArch64 musl executable, intentionally usable without
a dynamic interpreter. The auditor permits that one static runtime command only
when it has an executable ELF header, a load segment and no dynamic section.
Python/Node/uv/FFmpeg still require `/system/bin/linker64`; glibc linkage is always
rejected. This static contract is not an on-device kernel execution receipt.

Wheel inventory network failures stop preparation with an actionable retry
message; they cannot silently reclassify pure dependencies as native. The build
set is sorted before hashing. This makes the recorded classification depend on
the frozen versions and their wheel inventory, not transient DNS/HTTP failures.
