# Area Miner 0.25

Area Miner uses two player-position corners set with `/eio area pos1` and `/eio area pos2`.

Behavior:
- The higher selected Y is treated as the excavation surface.
- The miner never targets blocks above that surface.
- The first excavation slice is exactly the surface Y through surface Y - 4 (5 blocks).
- It clears the current 5-block slice before proceeding to the next slice.
- The next slice begins 5 blocks lower and this repeats until the configured total Depth is reached.
- Horizontal work is performed in parallel serpentine lanes within the selected X/Z rectangle.
- Area Miner has priority over Nuker and Chunk Miner to avoid input ownership conflicts.
- Normal Minecraft interaction-distance checks from Compatibility Guard still apply.
- Tool Saver and server-correction pauses remain respected.

Commands:
- `/eio area pos1`
- `/eio area pos2`
- `/eio area status`
- `/eio area clear`
