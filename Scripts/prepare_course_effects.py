from pathlib import Path
import unreal,runpy
root=Path(__file__).resolve().parents[1]
for name in ['prepare_character.py','prepare_external_assets.py','prepare_additional_attacks.py']:
    runpy.run_path(str(root/'Scripts'/name))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Reimport /Game/DasRogue/Pickups/BP_RogueCoinTestActor fields=archive_remove_with_dependencies')
runpy.run_path(str(root/'Scripts/prepare_course_world.py'))
