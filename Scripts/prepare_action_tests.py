import unreal
from pathlib import Path
import shutil
root=Path(r"C:/src/ActionRoguelikeDas")
shutil.copyfile(root/'Tests/Das/rogue_action_probe.das',root/'Content/Das/Scripts/rogue_action_probe.das')
shutil.copyfile(root/'Tests/Das/rogue_unrelated_object.das',root/'Content/Das/Scripts/rogue_unrelated_object.das')
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(w,'Das.DSL.Apply rogue_unrelated_object.das /Game/DasRogue/Tests/BP_RogueUnrelatedObject roguetest.RogueUnrelatedObject')
unreal.SystemLibrary.execute_console_command(w,'Das.DSL.Apply rogue_action_probe.das /Game/DasRogue/Tests/BP_RogueActionProbe roguetest.RogueActionProbe')
kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueActionProbe.BP_RogueActionProbe_C')
assert kind
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in list(actors.get_all_level_actors()):
 if a.get_class()==kind:actors.destroy_actor(a)
assert actors.spawn_actor_from_class(kind,unreal.Vector(0,0,-1000))
print('Action/GC probe ready; do not save this actor in gameplay map')
