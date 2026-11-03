from pathlib import Path
import runpy
import shutil
import unreal

root=Path(__file__).resolve().parents[1]
for filename in ['prepare_character.py','prepare_health_pickup.py','prepare_action_tests.py']:
    runpy.run_path(str(root/'Scripts'/filename))
shutil.copyfile(root/'Tests/Das/roguetest/rogue_pickup_probe.das',root/'Content/Das/Scripts/roguetest/rogue_pickup_probe.das')
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_pickup_probe.das /Game/DasRogue/Tests/BP_RoguePickupProbe roguetest.RoguePickupProbe')
assert unreal.load_class(None,'/Game/DasRogue/Tests/BP_RoguePickupProbe.BP_RoguePickupProbe_C')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
