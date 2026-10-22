# BLHermes on Android / Termux

## Current status

**Release acceptance pending. Production installation is currently unsupported.**
Substantial packaging, Android-native runtime and validation support exists;
there is no qualified production candidate from the current pass. This is not
evidence of a reproduced runtime defect. See the [engineering handoff](../BLHERMES_TERMUX_RELEASE.md).

## Intended target

The candidate targets aarch64 (arm64-v8a), ordinary unrooted Termux with the
standard `com.termux` application ID and `/data/data/com.termux/files/usr`
prefix. Run directly in Termux, not inside PRoot. Python wheels target
`android_24_arm64_v8a` / cp314. API 24 is a build target, **not an empirically
supported minimum Android version**. Minimum Android and tested Termux app
versions remain pending device qualification.

## Installation

Production installation instructions are not available yet. **PUBLIC APT
DISTRIBUTION: NOT PROVISIONED.** No BLHermes public repository URL or signing
fingerprint is established by this checkout. The upstream Nous feed distributes
upstream packages; do not install those as BLHermes. Do not use the desktop/server
installer or compile dependencies on your phone to repair a candidate.
Maintainers testing an independently verified candidate should follow the
[device acceptance procedure](termux-device-acceptance.md).

## First launch

After a maintainer has installed a verified candidate, run `hermes --version`,
`hermes --help`, then `hermes setup`. Start `hermes` for a conversation or
`hermes --tui` for the TUI. These are candidate acceptance steps, not a claim
that first launch has passed on Android.

## Provider configuration

Use `hermes setup` or `hermes model` to choose a provider and model. Enter your
own credentials through local setup; never paste API keys into bug reports or
shell command arguments. Provider network access and an authenticated streaming
turn still require device acceptance. Provider charges may apply.

## State location

State defaults to `$HOME/.hermes` inside private Termux storage. `HERMES_HOME`
and profiles select alternative private state locations. Settings live in
`config.yaml`; secrets live in `.env`. Sessions, skills and plugins also persist
in the selected profile. Back up private state locally before package changes;
backups contain secrets. Package files live under `$PREFIX/lib/hermes-agent`.

## Updates

APT/dpkg owns the candidate runtime. `hermes update` must refuse to overwrite
it. Once a BLHermes signed feed exists, updates will use `pkg update` and
`pkg upgrade hermes-agent`. Those commands do not establish or configure a feed.
Commit candidates have no self-update channel. A genuine N→N+1 transition is
still pending; same-version reinstall is not an upgrade test.

## Optional permissions

Base startup needs no shared-storage permission, root, Magisk, ADB or Termux:API.
Keep ordinary work in private storage. Grant Android storage or optional companion
app permissions only for a feature you deliberately enable; broad storage access
is not a base installation prerequisite.

## Gateway notes

Use `hermes gateway setup` and foreground `hermes gateway run` when testing a
reviewed adapter. Configure sender allowlists and authentication first; keep
local listeners on loopback. No systemd service is promised. Android can suspend
or kill Termux, including while the screen is off. Continuous background service
and every messaging adapter remain outside the current acceptance claim.

## Skills, plugins and MCP

Discovery/import validation covers infrastructure, not every integration.
Review executable content before enabling it. Native dependencies must support
Android/Bionic and the packaged Python ABI; desktop-only binaries will not work.
MCP children and plugins have the Termux user's authority. Use pinned, reviewed
integrations and verify cleanup, timeouts and cancellation on-device.

## Uninstall

After stopping sessions and gateway processes, `pkg uninstall hermes-agent`
removes package-owned runtime files. Removal and `apt purge hermes-agent` are
intended to preserve private profile state; neither is credential erasure.
Reinstall/state usability must still be verified on the candidate. Do not delete
state unless you separately intend to erase it and have a private backup.

## Troubleshooting

Save `hermes --version`, Android/API level, Termux version/source, architecture,
artifact hash, exact command, exit status and redacted errors. Never share `.env`,
API keys, full configuration or session databases. For a candidate installation,
run the installed validator from the acceptance guide. Stop on loader/import,
checksum or signature failures; report them instead of disabling checks or
installing replacement libraries into the managed package.

## Known limitations

No real candidate, Bionic install receipt or real-device acceptance was produced
in this pass. Package sizes remain unmeasured. Minimum Android version,
authenticated providers, upgrade behavior and phone UI remain unqualified.
Electron, local desktop computer use/Chromium, local Docker, nemo-relay exporter
and phone-native clipboard/microphone integrations are not certified targets.
The rolling build compiler packages also prevent a bit-for-bit reproducibility
claim. See the handoff for current evidence and blockers.

## Release acceptance status

Implementation status: **SOURCE COMPLETE — BUILD ENVIRONMENT REQUIRED**. A real package must pass static audit, Bionic
runtime and installed validation before device acceptance begins. Only successful
real Android acceptance can establish production support.

## Migrating an existing upstream Hermes installation

The Debian identity remains `hermes-agent`. A BLHermes candidate replaces an
upstream package with that identity; it cannot coexist as a second dpkg package.
APT selects by Debian version and configured origins, not the BLHermes branding.
Inspect `apt-cache policy hermes-agent` and `dpkg-query -W hermes-agent` before
installing an independently verified local candidate. A candidate older than the
installed version is a downgrade and requires a deliberate operator decision.
No `Conflicts`, `Breaks` or `Replaces` against the identical package name is needed.

Existing profile configuration, skills, memories and credentials are reused
when the same `HERMES_HOME` is selected. Back them up privately first. For final
acceptance use a fresh isolated profile, then separately verify a copy of old
state. Package installation does not convert or delete credentials. Ordinary
application config migrations run when that profile is opened.

Manual/source installs can coexist on disk but can shadow `hermes` on PATH.
Inspect `type -a hermes`, shell aliases/functions and `readlink "$PREFIX/bin/hermes"`.
Remove or move only a launcher you have identified and backed up; do not delete
its source checkout or state as a package repair. The package's post-install
script refuses to overwrite a foreign launcher. If this leaves dpkg awaiting
configuration, resolve only the identified launcher collision, run
`dpkg --configure hermes-agent`, then rerun the installed validator. An existing candidate reinstalls
idempotently; a real version increase uses dpkg's ordinary replacement semantics.

An observed upstream source can return 404 and prevent **all** APT updates:

```sh
grep -Rni "hermes-assets.nousresearch.com" "$PREFIX/etc/apt"
```

Review the matches locally: sources can contain private URLs. In the observed
case, `$PREFIX/etc/apt/sources.list.d/hermes-agent.list` contains
`hermes-assets.nousresearch.com/releases/termux/stable`. If that file contains
**only** the identified upstream Hermes source, move that single file to a
private backup outside APT's source directories, then run `pkg update` again.
If it mixes repositories, edit out only the identified entry instead. Never wipe
`sources.list.d` or replace unrelated repository configuration.

The old `$PREFIX/etc/apt/keyrings/hermes-agent.asc` may be removed only after
checking that no remaining `signed-by` entry refers to it and that it is the
identified upstream key. Keeping an unused key is preferable to deleting a key
still needed by another source. BLHermes never silently edits APT sources or
keys. The acceptance diagnostic reports matching source **filenames**, never
automatically removes them, and does not claim that every upstream URL is stale.

## Runtime environment and state ownership

| Item | Owner and contract |
| --- | --- |
| App, Python/Node, native libraries, TUI, bundled skills/plugins, bundled tools | PACKAGE OWNED under `$PREFIX/lib/hermes-agent`; command symlinks under `$PREFIX/bin`; replaced by dpkg. Do not edit these files. |
| Settings, MCP/gateway settings, provider/model selection | USER OWNED `config.yaml` and related files in selected private profile. |
| Credentials and authorization | USER OWNED `.env`, `auth.json` and provider/token stores in private state; not diagnostic attachments. |
| Conversations, memories, cron jobs, installed skills/plugins, logs | USER OWNED `state.db`, `sessions/`, `memories/`, `cron/`, `skills/`, `plugins/`, `logs/` within the selected profile; preserved on upgrade/remove/purge. Cron execution requires a running process; Android suspension can delay or prevent it. |
| Downloaded PM/plugin artifacts and caches | USER OWNED `<data-root>/tools`, `<data-root>/cache/partials` and `<data-root>/installs/<install-key>`; package purge does not erase them. Bundled PM tools remain package owned. |
| Python bytecode | EPHEMERAL `${PYTHONPYCACHEPREFIX}` or `${XDG_CACHE_HOME:-$HOME/.cache}/hermes-pycache`; safe to regenerate. |
| Scratch files and acceptance state | EPHEMERAL private `TMPDIR` (default `$PREFIX/tmp`); acceptance creates and removes only its own unique directory. |

`<data-root>` is the profile-aware root returned by `get_default_hermes_root()`
(default `$HOME/.hermes`); `<install-key>` is PM's SHA-derived key for the owning
application path. The sealed tool store resolves to the package's `tools/`;
new writable tool downloads use the data-root store. Credential backends can
also use deliberately configured external private stores. These are user owned.

`HOME` must be an absolute private directory. `PREFIX` defaults to the standard
prefix and any other value is refused. `HERMES_HOME`, when set, must be absolute;
otherwise the normal profile resolver uses `$HOME/.hermes`. `TMPDIR` must be
absolute and writable. Missing `PATH` defaults to `$PREFIX/bin`; bundled Node,
npm (implementation tooling), FFmpeg and rg are prepended by the launcher.
`SHELL`, `LANG` and `TERM` default to prefix `sh`, `C.UTF-8` and `xterm-256color`.
`LC_*` and `COLORTERM` remain optional terminal/locale hints; no shell startup
file is required. Invalid explicit locale settings should be corrected locally.
Shared-storage filesystems are unsuitable for executable package/state trees.
TLS uses the Termux trust store; an empty/unreadable store fails the runtime gate
with instructions to check `ca-certificates` and `SSL_CERT_FILE`/`SSL_CERT_DIR`.

## Safe failure evidence

After installing a verified candidate, collect a facts-only private JSON bundle:

```sh
root="$PREFIX/lib/hermes-agent"
"$root/bin/hermes" --version
# Use the validator environment block in the device worksheet for this Python.
PYTHONPATH="$root/app" \
LD_LIBRARY_PATH="$root/tools/python$PREFIX/lib:$root/tools/node$PREFIX/lib:$root/tools/ffmpeg$PREFIX/lib:$root/runtime-libs/lib:$PREFIX/lib" \
"$root/venv/bin/python" "$root/app/scripts/termux/device_acceptance.py" \
  --safe --output "$HOME/blhermes-acceptance.json"
```

Use a new output filename each time. `--safe` runs offline checks with temporary
HOME/state, no keys, provider calls, package changes or external services. Without
`--safe`, it gathers facts and CLI/package checks only. PASS / FAIL / SKIP remain
separate. This receipt is not complete device acceptance. It deliberately excludes
application logs, configuration, environment dumps and conversation contents;
add a manually reviewed error excerpt separately if needed. A failed command's
exit code is retained without collecting arbitrary child output.

URL opening and clipboard/image/audio integrations are optional. Android's text
paste through the terminal remains available. If browser launch is unavailable,
open the displayed HTTPS URL manually. Desktop clipboard/image APIs and local
Chromium are not certified; missing clipboard support must not block startup.
Do not install Termux:API or grant storage permission merely to repair startup.
