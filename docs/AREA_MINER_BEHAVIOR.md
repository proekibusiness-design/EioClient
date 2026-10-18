# Area Miner excavation origin

The two selected coordinates define the X/Z excavation rectangle. The higher selected Y is the excavation surface. No block with Y above that surface may be selected by Area Miner.

On start, Area Miner works the first slice from `surfaceY` down through `surfaceY - 4`. It must finish that slice before progressing to the next 5-block slice. Subsequent slices are `surfaceY - 5` through `surfaceY - 9`, and so on until the requested total depth is reached.

Within a slice, excavation proceeds in straight serpentine lanes across the selected rectangle. The player reverses direction at an end boundary and shifts to the next lane rather than mining arbitrary nearby blocks.
