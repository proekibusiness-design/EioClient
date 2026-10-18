# Eio Client

Eio Client is a Fabric client project targeting **Minecraft 26.3** with **Java 25**.

Current release: **0.16.0** (`EIO-016-QA2`).

## Release highlights

- Compact 438x254 translucent glass ClickGUI opened with Right Shift.
- Seven categories: Combat, Movement, Player, Render, World, Testing, and Misc.
- **33 configurable modules** with persistent settings and stable Minecraft key mappings.
- New HUD/QoL tools in 0.16: **CPS**, **Keystrokes**, and **Held Item**.
- Runtime fault containment: unexpected client tick/HUD faults enter **Eio Safe Mode**, release Eio-owned input/flight/effect state, log diagnostics, and keep a minimal recovery HUD instead of repeatedly running the failing HUD path.
- `/eio recover` clears Safe Mode after the underlying issue has been addressed.
- `/eio selftest` validates the module model, key mappings/conflicts, config write access, and profile storage.
- Named config profiles: `/eio profile save <name>`, `/eio profile load <name>`, `/eio profile delete <name>`, and `/eio profile list`.
- Diagnostics are written to `config/eio-diagnostics.log`; `/eio doctor` reports build, model, config, Safe Mode, and runtime fault state.
- Right-clicking a module card resets that module's settings to declared defaults; right-clicking an individual setting resets only that setting.
- Main-menu rainbow `MADE BY EIO` branding, while the ClickGUI stays compact and minimal.
- Config backup/recovery plus atomic writes, schema 4 snapshots, deterministic reload-from-defaults behavior, and profile reuse of the same validated property model.
- Centralized input ownership/cleanup for movement, jump, sneak, follow, flight, combat timing, and injected Fullbright state.
- HUD telemetry for coordinates, FPS, health, speed, facing, rotation, memory, clock, session time, CPS, keystrokes, held item, inventory, durability, targets, waypoints, and active modules.
- Recovery/diagnostic commands include `/eio doctor`, `/eio selftest`, `/eio panic`, `/eio recover`, `/eio resetsettings`, and `/eio reloadconfig`.

## Build quality

GitHub Actions builds directly from the checked-in native Gradle/Fabric project. The permanent release pipeline is read-only and performs:

- static source/model/category/language-key validation;
- Java 25 + Fabric compilation;
- Fabric metadata and dependency checks;
- JAR integrity and duplicate-entry checks;
- compiled bytecode/feature verification;
- stable-key-ID checks;
- a second clean build that must be **byte-for-byte identical** to the first.

Temporary release transformers are removed after canonicalization; the repository does not rely on legacy patch scripts or bundled project ZIPs to build a release.
