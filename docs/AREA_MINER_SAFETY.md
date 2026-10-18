# Area Miner safety guarantees

- Area Miner never targets blocks above the configured surface Y.
- Area Miner never targets blocks outside the selected X/Z rectangle.
- Area Miner only works inside the current 5-block slice.
- Compatibility Guard's vanilla block-interaction-range predicate remains authoritative.
- Tool Saver still gates mining automation.
- Area Miner has mining-input priority over Nuker and Chunk Miner when enabled.
