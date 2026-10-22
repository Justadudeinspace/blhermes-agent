---
sidebar_position: 3
title: "Android / Termux"
description: "BLHermes Agent Termux release status and candidate installation"
---

# BLHermes on Android with Termux

:::danger Termux is currently broken
The existing Termux distribution remains unsupported. This fork has not yet
produced and accepted a release on a clean Android device. Do not rely on it
for production use. A passing Linux test or container build does not change
this status.
:::

BLHermes targets **aarch64 (arm64-v8a)** Android with the standard Termux
application and prefix `/data/data/com.termux/files/usr`. The wheel target is
Android API 24 or newer; the effective minimum OS must also satisfy the pinned
Termux runtime packages. That minimum has not yet been certified on a device.
Other architectures, renamed Termux application IDs, rooted environments and
Linux/PRoot installations are outside this candidate acceptance target.

The intended installation method is a **signed APT repository**. The fork's
repository URL and signing-key fingerprint have not yet been provisioned and
verified. Nous Research's `hermes-assets.nousresearch.com` feed distributes
upstream artifacts; it is not a BLHermes package source.

## Candidate installation

Wait for a release maintainer to publish the BLHermes repository URL, public
key URL, independently verified fingerprint, and suite. With those published
values, the installation procedure is:

```sh
pkg update
pkg install curl gnupg ca-certificates
mkdir -p "$PREFIX/etc/apt/keyrings"
# Replace these values with the published BLHermes release values.
repo_url='https://REPLACE-WITH-BLHERMES-REPOSITORY'
key_url="$repo_url/key.asc"
suite='hermes-stable'
curl -fSL "$key_url" -o "$PREFIX/etc/apt/keyrings/blhermes.asc"
gpg --show-keys --with-fingerprint "$PREFIX/etc/apt/keyrings/blhermes.asc"
```

Compare the displayed primary fingerprint to the maintainer's independently
published fingerprint. Stop on a mismatch. After verification:

```sh
printf 'deb [signed-by=%s/etc/apt/keyrings/blhermes.asc] %s %s main\n' \
  "$PREFIX" "$repo_url" "$suite" > "$PREFIX/etc/apt/sources.list.d/blhermes.list"
pkg update
pkg install hermes-agent
hermes --version
hermes
```

Complete first-run setup and select a provider and model. Use `hermes setup`
to revisit configuration; use `hermes --tui` to explicitly select the TUI.
Supply your own provider credentials through setup. Never put keys in bug
reports or shell command arguments. Network/provider subscriptions are separate.

The package includes Python, Node, npm, uv, ripgrep, FFmpeg and native runtime
libraries. Base installation must not require Git, Python compilation,
manual pip commands, or PATH repair. Use the Termux app's normal shell.

## State and updates

Package files live in `$PREFIX/lib/hermes-agent`; launchers live in
`$PREFIX/bin`. User configuration, credentials, conversations, skills, plugins
and logs live under the profile-aware BLHermes home (normally `$HOME/.hermes`,
or an explicitly selected `HERMES_HOME`). Keep this in Termux private storage.
Back up user state before upgrades; backups contain secrets and need protection.

```sh
pkg update
pkg upgrade hermes-agent
```

APT owns these files. `hermes update` refuses to change an APT installation.
Commit test builds refuse channel updates too; replace them through APT/dpkg.

## Gateway

Run the gateway in a Termux terminal:

```sh
hermes gateway run
```

Configure adapter credentials and allowed senders before use. Verify any local
HTTP listener binds only to loopback unless you deliberately configure remote
access. Stop with Ctrl+C and verify the process exits. This package does not
install a system service. Android may kill or suspend background processes;
a wake lock or battery exemption does not guarantee availability. Foreground
start/stop and background behavior still require device acceptance.

## Skills, plugins and MCP

Use the normal BLHermes skill, plugin and MCP configuration workflows. Pure
Python integrations and Android-compatible subprocesses are candidate targets;
native dependencies must support Bionic and the bundled Python ABI. A discovered
manifest or import test does not establish that an integration works. Review
third-party code before enabling it: plugins and MCP subprocesses can operate
with your Termux user's filesystem and credentials.

## Optional permissions and limits

Base chat, state and private files require no shared-storage permission.
Only run `termux-setup-storage` when you deliberately need Android shared
storage. Termux:API features require the matching Android add-on and permissions;
the package does not supply phone microphone or clipboard adapters.

Electron, local Chromium, desktop computer use and a local Docker daemon are
outside the package contract. The `nemo-relay` exporter is excluded by the
existing Android build policy. Voice, arbitrary native plugins and third-party
MCP binaries need separate Android compatibility checks. Python reports
`sys.platform == "android"`; a Linux-only integration may be unavailable.

## Uninstall and troubleshooting

```sh
pkg uninstall hermes-agent
```

Removal deletes the packaged runtime and owned launchers. Both removal and
APT purge preserve profile/user state; neither erases conversations or keys.
Deleting that state is a separate, deliberate user action. A reinstall uses
existing state.

- Package not found: check the published BLHermes source and run `pkg update`.
- Signature failure: verify the key and URL; never bypass signature checking.
- Missing interpreter/library/TUI: reinstall with `apt reinstall hermes-agent`
  and report the package version and complete error. Do not patch installed code.
- TLS failure: check Android date/time, connectivity and `ca-certificates`.
- Invalid key: revisit `hermes setup` and verify the provider/account; redact keys.
- Missing storage access: grant it only for the attempted shared-storage feature.
- Gateway stops with the screen off: check Android background-process limits.

Run `hermes doctor` for diagnostics. Maintainers must complete the repository's
`BLHERMES_TERMUX_RELEASE.md` acceptance procedure before changing this warning.
