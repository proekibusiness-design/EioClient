# Eio Client

Eio Client is a Fabric client project targeting **Minecraft 26.3** with **Java 25**.

Current release: **0.15.0** (`EIO-015-QA2`).

## Release highlights

- Compact 438x254 translucent glass ClickGUI opened with Right Shift.
- Seven categories: Combat, Movement, Player, Render, World, Testing, and Misc.
- 30 configurable modules with persistent settings and stable Minecraft key mappings.
- Main-menu rainbow `MADE BY EIO` branding, while the ClickGUI stays compact and minimal.
- Config backup/recovery plus atomic writes and deterministic reload-from-defaults behavior.
- Centralized input ownership/cleanup for movement, jump, sneak, follow, and flight state.
- HUD telemetry for coordinates, FPS, health, speed, facing, rotation, memory, clock, session time, inventory, durability, targets, waypoints, and active modules.
- Recovery/diagnostic commands: `/eio doctor`, `/eio panic`, `/eio resetsettings`, and `/eio reloadconfig`.
- Reproducible Gradle builds: CI performs two clean builds and requires byte-for-byte identical JAR output.

## Build

GitHub Actions runs static model checks, Java compilation, JAR integrity checks, Fabric metadata checks, bytecode/feature checks, stable-key checks, and a reproducibility check before uploading a release artifact.

The repository is a native Gradle/Fabric project; it no longer relies on legacy source-patching scripts or a bundled project ZIP.
