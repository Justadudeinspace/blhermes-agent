# Building the Termux distribution

This is operator documentation. End users install a signed APT package; they
never build Python, wheels, or the frontend on their phone. Support remains
blocked pending the release gates in `BLHERMES_TERMUX_RELEASE.md`.

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

The complete A–M device procedure and outstanding gates live in
`BLHERMES_TERMUX_RELEASE.md`. Container results never count as Android device UX
or authenticated model acceptance.
