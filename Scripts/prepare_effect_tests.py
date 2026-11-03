"""Apply an observable periodic effect for the real-PIE timer/stack regression."""
from pathlib import Path
import shutil
import unreal
root=Path(__file__).resolve().parents[1]
name='rogue_periodic_effect.das'
shutil.copyfile(root/'Tests/Das/roguetest'/name,root/'Content/Das/Scripts/roguetest'/name)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply '+name+' /Game/DasRogue/Tests/BP_RoguePeriodicEffect roguetest.RoguePeriodicEffect')
assert unreal.load_class(None,'/Game/DasRogue/Tests/BP_RoguePeriodicEffect.BP_RoguePeriodicEffect_C')

name='rogue_fixed_duration_effect.das'
shutil.copyfile(root/'Tests/Das/roguetest'/name,root/'Content/Das/Scripts/roguetest'/name)
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply '+name+' /Game/DasRogue/Tests/BP_RogueFixedDurationEffect roguetest.RogueFixedDurationEffect')
assert unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueFixedDurationEffect.BP_RogueFixedDurationEffect_C')
