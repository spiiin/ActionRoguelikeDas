from pathlib import Path
import runpy
import unreal
scripts=Path(__file__).parent
runpy.run_path(str(scripts/'prepare_additional_attacks.py'))
runpy.run_path(str(scripts/'prepare_action_tests.py'))
runpy.run_path(str(scripts/'prepare_effect_tests.py'))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_burning_target.das /Game/DasRogue/Tests/BP_RogueBurningTarget roguetest.RogueBurningTarget')
assert unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueBurningTarget.BP_RogueBurningTarget_C')
# This is the playable class used by both player and AI attacks.
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Reimport /Game/DasRogue/BP_MagicProjectileDemo')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
