# Coin spawning performance (2026-11-05)

Real PIE on the original-layout course map, 1000 coins per lever activation.
Timings are game-thread CPU measurements on this workstation, not frame-rate targets.

| Implementation | Complete spawn |
| --- | ---: |
| Original DAS implementation | 4548–4758 ms |
| Direct navigation batch + direct ISM arrays | 2176–2446 ms |
| One mutable draft for generated container packing | 72–77 ms |
| Typed contiguous numeric/math array transport | 6.20–6.56 ms |

Final navigation: 1.37–1.59 ms. Final add-only call: 3.94 ms. Native ISM insertion
alone (including Python's native argument transport): 1.12 ms. The 100-coin warmup
is excluded from the final range; it includes first-use overhead.

The generated container packer resized an immutable carrier to the complete array
length, then copied that carrier again for every element. Work therefore grew
quadratically. Generated non-plain containers now use one `ue_struct_edit` draft.
Numeric and native math arrays pack/unpack with checked contiguous native copies;
object references, class references, names, strings and maps keep their ownership
and token-aware codecs. Native navigation and ISM adapters avoid per-element
reflected calls and string property paths. The coin total also accumulates locally
and writes its reflected field once per batch.

```das
var locations : array<UEVector>
with_ue_navigation() $(navigation : NavigationSystemRef) {
    locations <- ue_navigation_random_points(navigation, origin, radius, count)
}
```

The block is an ordinary DAS function. Navigation references remain checked,
context-owned handles. Batch queries preserve the example's origin fallback for
failed points. All coin rules, amounts, collection and loot remain DAS gameplay.

Validation: `rogue-coins-plain-v10-20261105`, suites `container-transport` and
`rogue-coin-profile`, PASS. The PIE suite includes ten checks: real lever input,
1000 ISM coins, original coin mesh/material/audio, collection, int64 wallet, loot,
scoped/batched navigation, missing navigation, invalid count and stable ISM IDs.
Temporary timings were removed from production gameplay after profiling.
Local detailed receipts are in `Saved/Tests/course_coin_profile_final_bulk.json`
and `Saved/Tests/rogue_coin_profile_pie.json`.
