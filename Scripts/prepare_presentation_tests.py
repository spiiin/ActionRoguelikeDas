"""Authored fallback variants preserve the DSL default validation contract."""
from pathlib import Path
import shutil
import unreal
root=Path(__file__).resolve().parents[1]

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for name,filename in [('RogueWithoutPresentation','rogue_without_presentation.das'),('RogueMissingPresentation','rogue_missing_presentation.das')]:
    shutil.copyfile(root/'Tests/Das'/filename,root/'Content/Das/Scripts'/filename)
    unreal.SystemLibrary.execute_console_command(world,f'Das.DSL.Apply {filename} /Game/DasRogue/Tests/BP_{name} roguetest.{name}')
    assert unreal.load_class(None,f'/Game/DasRogue/Tests/BP_{name}.BP_{name}_C')
