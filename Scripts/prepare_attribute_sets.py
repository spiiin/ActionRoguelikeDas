"""Create the reflected attribute enum and ScriptObject class hierarchy before consumers."""
from pathlib import Path
import unreal
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Types.Apply rogue_attribute_types.das /Game/DasRogue/Types')
for name in ('RogueAttributeSet','RogueHealthAttributeSet','RoguePawnAttributeSet','RoguePlayerAttributeSet','RogueMonsterAttributeSet'):
    unreal.SystemLibrary.execute_console_command(world,
        f'Das.DSL.Apply rogue_attribute_set.das /Game/DasRogue/Attributes/BP_{name} rogue.{name}')
    assert unreal.load_class(None,f'/Game/DasRogue/Attributes/BP_{name}.BP_{name}_C'),name+' failed to import'
print('DAS_ATTRIBUTE_SETS_PREPARED')
