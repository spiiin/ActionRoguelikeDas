"""Prepare common gameplay, the separate patrol map and its test observer."""
from pathlib import Path
import runpy
import unreal

root=Path(__file__).resolve().parents[1]
# Reconcile pre-existing dummy declarations after callback annotation changes.
# These assets share a source but all can be loaded by the cloned test level.
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
for target in ['/Game/DasRogue/BP_RogueTargetDummy','/Game/DasRogue/BP_TargetDummy',
               '/Game/DasRogue/Tests/BP_RogueTargetDummy']:
    if assets.does_asset_exist(target):
        unreal.SystemLibrary.execute_console_command(world,
            'Das.DSL.Apply rogue_target_dummy.das '+target+' roguedemo.RogueTargetDummy')
for filename in ['prepare_character.py','prepare_ai.py','prepare_patrol.py','prepare_action_tests.py']:
    runpy.run_path(str(root/'Scripts'/filename))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_patrol_probe.das /Game/DasRogue/Tests/BP_RoguePatrolProbe roguetest.RoguePatrolProbe')
assert unreal.load_class(None,'/Game/DasRogue/Tests/BP_RoguePatrolProbe.BP_RoguePatrolProbe_C')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
