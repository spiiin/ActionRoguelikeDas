"""Import the gameplay effect before projectiles resolve its strong class default."""
import unreal
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for source,name in [('rogue_action_effect','RogueActionEffect'),('rogue_action_effect_burning','RogueActionEffectBurning')]:
    path='/Game/DasRogue/Actions/BP_'+name
    unreal.SystemLibrary.execute_console_command(world,f'Das.DSL.Apply {source}.das {path} rogue.{name}')
    assert unreal.load_class(None,path+'.BP_'+name+'_C'),name
