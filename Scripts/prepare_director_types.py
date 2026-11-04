"""Compile the director's contracts before importing its runtime classes."""
import unreal
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Types.Apply rogue_director_types.das /Game/DasRogue/Types')
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Interfaces.Apply rogue_director_host.das /Game/DasRogue/Types')
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
for source,name in [('rogue_director_config','RogueDirectorConfig'),('rogue_director_slot','RogueDirectorSlot'),('rogue_spawn_director','RogueSpawnDirector')]:
    path='/Game/DasRogue/Director/BP_'+name
    unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Reimport '+path if assets.does_asset_exist(path) else 'Das.DSL.Apply '+source+'.das '+path+' rogue.'+name)
    assert unreal.load_class(None,path+'.BP_'+name+'_C'),name+' import failed'
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
print('DAS_DIRECTOR_TYPES PASS')
