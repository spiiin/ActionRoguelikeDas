# Editor module cache: historical crash and re-enable verification

The project currently enables `[ConsoleVariables] das.EditorModuleCache=1` in
`Config/DefaultEngine.ini`. The old cache was preserved under
`Saved/Das/ModuleCache.before-enable-20261105` before re-enabling it.
The original workaround and reproduction below are historical.

With the disk cache enabled, job `rogue-combat-parity-v4-20261104` requested
1,881,019,372,055 bytes before PIE while applying the attribute hierarchy.
The process still had about 32 GiB physical memory available. It was not a
normal RAM-capacity failure.

Moving `Saved/Das/ModuleCache` to
`Saved/Das/ModuleCache.before-combat-bindings-20261104` allowed attribute
compilation in `rogue-combat-parity-v5-20261104`. That run stopped later on a
missing bindings import in the new hit-flash component, subsequently fixed.
The next warm run `rogue-combat-parity-v6-20261104` again failed with a huge
allocation, before the gameplay test. The preserved streams and logs have not
been deleted.

Reproduction for the optimization work: enable `das.EditorModuleCache=1` in this
project, then run `rogue-combat-parity` twice through the shared build agent.
The preparation performs `prepare_external_assets.py`, then
`prepare_character.py` -> `prepare_attribute_sets.py`. The last successful
console marker is `DAS_TYPES_APPLY PASS`; the next calls apply the
`rogue_attribute_set.das` ScriptObject hierarchy. Compare cold and warm runs.
The current test bootstrap logs the actual setting as `DAS_COMBAT_MODULE_CACHE`.

The build also briefly failed because the parallel source-batch integration had
not yet materialized `DasEditorSourceBatch.inl`. It appeared when that integration
finished; no source-cache implementation was changed by the combat work.

The re-enable check passed all 13 combat checks on a cold cache. Its first warm
run completed compilation without payload rejection, then failed the player
hit-overlay timeout assertion. The subsequent shared-module integration run
`editor-shared-modules-v6-20261105` passed all 13 combat and 11 course-world
checks. The separate disk-cache suite also passed cold, warm and fresh-process
reopen checks, including zero rewrites for an unchanged warm stream. These
results do not establish the original oversized allocation root cause. See `Saved/Tests/combat_module_cache_reproduction.json`
for the local diagnostic receipt. This file records an isolation and workaround,
not a root-cause fix in the cache serializer.

The overlay assertion was reproduced with diagnostic fields: the controlled hit
was at game time 2.2667, another hit occurred at 2.7500, and the test asserted the
overlay was hidden at 3.3667. The flash counter was 4 instead of the expected 3.
The timer was correctly restarted by extra damage; this is not evidence of a
cache or timer-dispatch failure. The combat fixture now removes remaining
projectiles and active periodic effects from the preceding real-shot check
before testing the two controlled hits, and verifies the hit count is unchanged.

Final verification: `editor-shared-world-final-20261105` passed 11 course-world
checks and `editor-shared-combat-isolated-20261105` passed all 13 combat checks.
The isolated overlay observation recorded two flashes for two controlled hits,
no later damage, and Visible=false at 1.1 seconds after the final hit. No
production timer behavior was changed. Per-pass compiler timing was disabled
after recording measurements; disk caching remains enabled.
