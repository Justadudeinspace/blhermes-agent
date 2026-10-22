# Termux device acceptance worksheet

**All tests below are pending. This is a procedure, not a test receipt.**
Production installation is unsupported. Use an ordinary unrooted aarch64 Termux
installation with the standard `com.termux` prefix. No Magisk, ADB, PRoot or
shared-storage permission is required. Minimum Android version is unqualified;
`android_24_arm64_v8a` is a build target only.

The maintainer must first supply an actual candidate, its independently verified
SHA-256, source commit and successful static/Bionic/container receipts. No public
BLHermes feed or signing fingerprint is provisioned here. Do not substitute the
upstream Nous feed. Direct local candidate installation below does not qualify
a public signed-feed release. Stop at any failed prerequisite.

Record device model, Android/API version, Termux version/source, package version,
source commit and archive hash. Keep evidence in private Termux storage. Review
logs before sharing: exclude credentials, full config and session databases.
Use a fresh Termux test installation; never remove an existing user's state.

```sh
export PREFIX=/data/data/com.termux/files/usr
mkdir -p "$HOME/blhermes-acceptance"
cd "$HOME/blhermes-acceptance"
export HERMES_HOME="$PWD/state"
mkdir -p "$HERMES_HOME"
chmod 700 "$HERMES_HOME"
```

For every command save its exit status and redacted output if it fails. For UI
actions save dimensions, action sequence and the visible error; do not capture
credential entry. Mark each row PASS / FAIL / BLOCKED with evidence, never infer
success from another test.

| Test | Command / action | Expected result | Save on failure |
| --- | --- | --- | --- |
| 1 — Clean environment | `uname -m; getprop ro.build.version.release; getprop ro.build.version.sdk; termux-info; df -h "$HOME"; dpkg-query -W hermes-agent` | aarch64, standard prefix, enough free space; package absent in this fresh test app (the final query is expected to fail before install). Record actual OS/app versions. | Platform output and conflicting package inventory. |
| 2 — Package installation | Place the independently supplied candidate in private storage. `read -r -p 'Candidate absolute path: ' deb`; `read -r -p 'Expected SHA-256: ' expected`; run the hash-verification block below; then `apt install "$deb"`; `dpkg-query -W hermes-agent` | Exact hash matches, install succeeds without root or manual runtime repair. Stop on mismatch. | Hash comparison, APT output, package metadata. |
| 3 — Installed validator | Run the validator block below. | Exit 0, `BIONIC_RUNTIME_CONTRACTS_OK`, `INSTALLED_BUNDLE_VALIDATION_OK`; no leaked child. | Complete redacted validator log and exit code. |
| 4 — First boot | `hermes --version; hermes --help; hermes chat --help; hermes setup`; then `hermes --tui`. Exercise 120×24, 80×24 and 40×20 where available, resize/rotate, edit input, Ctrl+C, exit. | Version agrees with candidate, setup actions accessible, no catastrophic wrapping/crash, clean PTY/child shutdown. | Dimensions, UI actions, startup errors, leftover process list. |
| 5 — Provider configuration | Use `hermes model` / `hermes setup` locally with your own credentials. Restart. | Provider/model persists in isolated state. No secret printed; no CLI key arguments. | Provider name, redacted error and exit status. |
| 6 — Real streaming model turn | `hermes chat --oneshot -q 'Reply with the single word READY.'`; then interactive `hermes` and send a longer response request, cancel and retry. | Real authenticated response, incremental streaming, bounded cancellation and recovery. Charges may apply. | Redacted request/error, streaming/cancel timing, provider/model. |
| 7 — Safe terminal tool | In `hermes`, request terminal execution of `pwd` in the acceptance directory. | Actual terminal tool result, correct private directory, normal approval behavior. | Tool result and approval sequence. |
| 8 — Safe file tool | Ask the agent to create `proof.txt` containing `termux acceptance`, then read it through the file tool. After exit run `cat proof.txt`. | Exact text, no files outside the acceptance directory modified. | Tool output, path, file contents and approval behavior. |
| 9 — State persistence | Exit/restart `hermes`, inspect/resume the test conversation and provider selection. | State belongs to the explicit `HERMES_HOME`; conversation/config and proof file survive. | Redacted session identifier and observed loss/error. |
| 10 — Skill | `hermes skills list`; invoke one reviewed Android-compatible bundled skill in a conversation. | Readable metadata, actual skill behavior; user skill directory writable when used. | Skill name, metadata/load error, tool result. |
| 11 — Plugin infrastructure | `hermes plugins list`; review and exercise one compatible plugin through the documented plugin CLI; restart. Deliberately try an unsupported integration in a disposable profile. | Discovery/persistence works; unsupported platform fails clearly. This does not certify all plugins. | Plugin/version, platform decision and redacted failure. |
| 12 — MCP | Configure a maintainer-selected, reviewed, pinned read-only loopback MCP fixture using normal config; invoke its harmless tool, cancel/timeout, exit. | Discovery and real result, bounded errors, child cleanup. BLOCKED until a concrete fixture is supplied. | Fixture/version, bind address, redacted logs and process list. |
| 13 — Gateway | `hermes gateway setup`; configure one adapter with explicit sender allowlist/authentication; `hermes gateway run`. Exchange authorized test message, reject unauthorized sender, Ctrl+C. | Expected local listeners only, authorization enforced, clean shutdown. No systemd assumption. | Redacted startup/shutdown logs, listener addresses, child list. |
| 14 — Restart | Close/reopen Termux and run `hermes`; background/resume the app and repeat a turn. | Profile retained; lifecycle interruption recovers clearly. Android may kill the process; continuous service is not promised. | Lifecycle sequence, persisted-state result and startup errors. |
| 15 — Update | `hermes update` must refuse runtime replacement. With two genuine compatible candidates and an independently verified BLHermes signed test feed: `pkg update; pkg upgrade hermes-agent`; rerun test 3 and a real turn. | Refusal first; actual N→N+1 replacement preserves usable state. BLOCKED without two versions/feed; reinstall is not an upgrade. | Both versions/hashes, signature/APT logs, validator and state results. |
| 16 — Reinstall | Stop all sessions/gateway; `apt reinstall hermes-agent` only with a verified configured feed, otherwise `apt install --reinstall "$deb"`; rerun tests 3 and 9. | Same-version installation succeeds; state remains usable. | Maintainer-script output and state/validator results. |
| 17 — Remove | Stop sessions/gateway; `apt remove hermes-agent`; run removal checks below, then `apt purge hermes-agent`. Reinstall verified candidate and repeat test 9. | Package runtime/launchers gone; isolated state and proof survive removal/purge/reinstall. Package removal is not credential erasure. | Package output, remaining paths and state usability; never publish secret files. |
| 18 — Offline failure UX | Disable network temporarily; request a turn, cancel; restore network and retry. | Clear network failure, bounded cancellation, usable recovery. | Redacted message, elapsed time and child list. |
| 19 — Invalid API key UX | In a separate disposable `HERMES_HOME`, configure a deliberately invalid key through setup; request a turn, then return to the original profile. | Actionable authentication error, no key displayed, no damage to original state. | Redacted error, provider and exit status. |
| 20 — Optional permission UX | Start and perform private-storage file work without shared-storage permission or Termux:API. Only if deliberately testing storage, request access before granting it. | Base agent needs neither permission; optional feature denial is clear. Never broaden base permissions as a repair. | Requested feature, permission state and redacted error. |

Test 2 hash verification (literal runnable pipe):

```sh
printf '%s  %s\n' "$expected" "$deb" | sha256sum -c -
# Continue with apt install only after this command exits 0.
```

Test 3 installed validator (its own temporary state does not modify test 9 state):

```sh
root="$PREFIX/lib/hermes-agent"
PYTHONPATH="$root/app" \
LD_LIBRARY_PATH="$root/tools/python$PREFIX/lib:$root/tools/node$PREFIX/lib:$root/tools/ffmpeg$PREFIX/lib:$root/runtime-libs/lib:$PREFIX/lib" \
  "$root/venv/bin/python" -B "$root/app/scripts/termux/validate_installed.py" \
  > "$HOME/blhermes-acceptance/validator.log" 2>&1
validator_status=$?
cat "$HOME/blhermes-acceptance/validator.log"
printf 'validator exit: %s\n' "$validator_status"
```

Test 17 removal checks, before reinstall:

```sh
test ! -e "$PREFIX/lib/hermes-agent"
test ! -L "$PREFIX/bin/hermes"
test ! -L "$PREFIX/bin/hermes-agent"
test ! -L "$PREFIX/bin/hermes-acp"
test -d "$HERMES_HOME"
test "$(cat "$HOME/blhermes-acceptance/proof.txt")" = 'termux acceptance'
```

Keep test state until evidence review is complete. Purge must not erase profile
credentials. Do not include private backups in release artifacts.

A maintainer must reconcile all twenty results against the release gates in
[the engineering handoff](../BLHERMES_TERMUX_RELEASE.md). Static/host/mock tests
are not device passes. Public distribution additionally requires BLHermes-owned
signing/feed infrastructure and a real signed upgrade acceptance receipt.
