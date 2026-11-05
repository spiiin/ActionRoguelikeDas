from pathlib import Path
import runpy,unreal
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Reimport /Game/DasRogue/Pickups/BP_RogueCoinTestActor fields=archive_remove_with_dependencies')
runpy.run_path(str(Path(__file__).parent/'prepare_course_world.py'))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
path='/Game/DasRogue/Tests/BP_RogueBulkWorldProbe'
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
command='Das.DSL.Reimport '+path if assets.does_asset_exist(path) else 'Das.DSL.Apply rogue_bulk_world_probe.das '+path+' roguetest.RogueBulkWorldProbe'
unreal.SystemLibrary.execute_console_command(world,command)
assert unreal.load_class(None,path+'.BP_RogueBulkWorldProbe_C')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)

probe=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.load_class(None,path+'.BP_RogueBulkWorldProbe_C'),unreal.Vector(620,570,110))
assert probe
