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

Engineering status: **BLOCKED**. A real package must pass static audit, Bionic
runtime and installed validation before device acceptance begins. Only successful
real Android acceptance can establish production support.
