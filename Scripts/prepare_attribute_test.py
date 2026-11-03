"""Prepare the attribute regression actor after the standard character setup."""
import unreal
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_attribute_probe.das /Game/DasRogue/Tests/BP_RogueAttributeProbe roguetest.RogueAttributeProbe')
kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueAttributeProbe.BP_RogueAttributeProbe_C')
assert kind,'Attribute probe failed to import'
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in list(actors.get_all_level_actors()):
    if actor.get_class()==kind:actors.destroy_actor(actor)
assert actors.spawn_actor_from_class(kind,unreal.Vector(-1500,0,200))
