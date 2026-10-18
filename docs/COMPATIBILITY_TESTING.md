# EioClient 26.3 compatibility testing

This document tracks compatibility engineering for EioClient. It is not a bypass guide. A server-side anti-cheat flag is treated as diagnostic evidence: either the client violates vanilla semantics, the server/plugin has a false positive, or the environment is unsupported.

## Verified build environment

- Minecraft 26.3
- Java 25
- Fabric Loader 0.19.5
- Fabric API 0.163.0+26.3
- Fabric Loom 1.17.21
- `net.fabricmc.fabric-loom` (non-remapping Loom plugin)

Minecraft 26.1+ is unobfuscated, so the project does not require a Yarn/Intermediary mappings dependency for normal development. Fabric documents `net.fabricmc.fabric-loom` as the plugin for 26.1+ unobfuscated versions.

## Current architecture findings

- Eio has no custom packet sender or packet queue. Combat uses `MultiPlayerGameMode.attack`; mining automation drives the normal attack key; movement modules alter client input/state/velocity.
- Server position packets are now observed passively through `ClientPacketListener.handleMovePlayer`. Eio never cancels or rewrites those packets.
- Compatibility Guard uses Minecraft's own player interaction-range predicates before automated entity attacks and Chunk Miner/Nuker target selection.
- After a server position correction/teleport, Eio releases only inputs/state it owns and yields automation for a short configurable period.
- Speed and Fly are permission-sensitive. They intentionally change movement/abilities beyond ordinary vanilla survival movement and are not claimed compatible with anti-cheat-protected servers unless the server explicitly permits/configures them.

## Compatibility matrix

| Environment | Current status | What is verified | What still requires runtime testing |
| --- | --- | --- | --- |
| Vanilla single-player / integrated server | Build-supported | 26.3 compile, interaction API usage, unit tests | Launch world; module-by-module behavior; save/reload; death/dimension transitions |
| LAN world | Build-supported, runtime pending | Same protocol/client code path compiles | Host/join test; reconnect; position correction telemetry |
| Vanilla/private dedicated 26.3 | Build-supported, runtime pending | No custom packet spoofing; server-authority guard compiles | Real network latency, corrections, disconnect reasons, module combinations |
| Grim | Not universally compatible | Public Grim docs explicitly identify vanilla-rule/packet-order/movement violations as incompatibilities; Eio now guards reach and yields after server corrections | Exact Grim build + PacketEvents + server version; `/grim verbose`/debug output on authorized test server |
| Matrix | Version-specific test required | Matrix documents combat/movement/fast-break checks and a formal false-positive reporting workflow | Matrix's published supported-version table must match the actual 26.3 server deployment; capture `/matrix verbose` and plugin/server versions |
| Vulcan | Version-specific test required | Vulcan is PacketEvents-based and documents a support process for false positives | Exact Vulcan + PacketEvents versions on 26.3; capture alerts/logs and reproduction steps |

## Module risk classification

### Normally client-side / low protocol risk

HUD/render modules, coordinates, FPS, health, clock, memory, waypoints display, notifications, config/profile UI.

### Automated but intended to remain inside vanilla interaction semantics

Auto Clicker, Kill Aura, Trigger Bot, Chunk Miner and Nuker are constrained by Compatibility Guard where applicable. This does **not** make automation acceptable on a server whose rules prohibit it.

### Server-permission-sensitive

- Speed
- Fly
- Creative Assist where the server has not granted flight
- Any configured automation prohibited by the server's rules

Compatibility Guard does not disguise these modules. If a server rejects or corrects them, the correct response is to disable the module or obtain administrator support/configuration.

## Reproducible manual procedures

### A. Single-player baseline

1. Start a new vanilla-style 26.3 world with only Fabric API + EioClient.
2. Run `/eio selftest` and `/eio doctor`; save the output.
3. Test each module individually for 60 seconds.
4. For movement modules, test walking, sprinting, jumping, water, item use, knockback and dimension travel.
5. For mining, test normal blocks, unbreakable blocks, tool durability boundary, target loss and GUI open/close.
6. Save/reload the world, reconnect, and verify no owned key remains stuck.

### B. LAN

1. Open the baseline world to LAN and join from a second vanilla 26.3 client.
2. Repeat Follow/combat/mining interactions against the second player only where authorized.
3. Disconnect/reconnect both clients and verify Eio releases owned inputs.
4. Record `eio-diagnostics.log` and both `latest.log` files.

### C. Private dedicated server

1. Use a clean 26.3 server first, without anti-cheat.
2. Record baseline corrections/disconnects for each module.
3. Add one anti-cheat at a time; never stack anti-cheats during diagnosis.
4. Keep server version, plugin version, PacketEvents version, client version and exact Eio settings in the test record.
5. When a flag occurs, reproduce with the module off. Then reproduce with only that module enabled.

### D. Grim authorized test server

Capture `/grim verbose`; for movement prediction also capture `/grim debug` or console debug. Compare predicted vs actual movement and keep the exact client/server versions. Do not tune Eio to hide a violation; determine whether the client departed from vanilla movement or whether the anti-cheat has a reproducible false positive.

### E. Matrix authorized test server

Capture `/matrix verbose`, server/client/Matrix versions, and a first-person reproduction. Matrix's own bug-report guidance asks for these items for false positives.

### F. Vulcan authorized test server

Capture Vulcan/PacketEvents/server versions, alerts/logs, video and exact reproduction steps. Vulcan's official FAQ recommends disabling the affected check during investigation and filing the evidence with support for confirmed false positives.

## Required evidence for unresolved issues

Attach or provide:

- client `latest.log` and crash report if any;
- `config/eio-diagnostics.log`;
- disconnect/kick reason verbatim;
- server log around the event;
- anti-cheat verbose/alert output;
- server implementation/version and plugin versions;
- enabled Eio modules and their exact settings;
- a minimal reproduction sequence.
