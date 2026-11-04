# Warm editor module-cache crash observed during combat parity work

The project temporarily sets `[ConsoleVariables] das.EditorModuleCache=0` in
`Config/DefaultEngine.ini`. This is project-local; the wrapper implementation,
source-snapshot batch cache and resident compiled-program cache are unchanged.

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

Re-enable the project disk cache after the warm reproduction is fixed and the
full combat PIE suite passes twice. See `Saved/Tests/combat_module_cache_reproduction.json`
for the local diagnostic receipt. This file records an isolation and workaround,
not a root-cause fix in the cache serializer.
