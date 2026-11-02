"""Run outside PIE before Tests/verify_character_combat_pie.py; remove probe after testing."""
from pathlib import Path
import shutil
root=Path(r"C:/src/ActionRoguelikeDas")
shutil.copyfile(root/'Tests/Das/rogue_combat_probe.das',root/'Content/Das/Scripts/rogue_combat_probe.das')
import unreal
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(w,'Das.DSL.Apply rogue_combat_probe.das /Game/DasRogue/Tests/BP_CombatProbe roguetest.CombatProbe')
kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_CombatProbe.BP_CombatProbe_C')
assert kind
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actors.get_all_level_actors():
 if a.get_class()==kind:actors.destroy_actor(a)
probe=actors.spawn_actor_from_class(kind,unreal.Vector(0,0,-1000),transient=False)
assert probe
print('combat probe ready')
