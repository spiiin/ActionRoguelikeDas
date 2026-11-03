"""Editor-only assembly. Collection, healing and respawn are implemented in DAS."""
import unreal

editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
assert not editor.get_game_world(),'Prepare outside PIE'
world=editor.get_editor_world()
for source,name,identity in [
    ('rogue_pickup_actor','BP_RoguePickupActor','rogue.RoguePickupActor'),
    ('rogue_health_pickup','BP_RogueHealthPickup','rogue.RogueHealthPickup'),
    ('rogue_health_pickup_demo','BP_HealthPickupInteract','roguedemo.RogueHealthPickupDemo'),
]:
    path='/Game/DasRogue/Pickups/'+name
    unreal.SystemLibrary.execute_console_command(world,f'Das.DSL.Apply {source}.das {path} {identity}')
    assert unreal.load_class(None,path+'.'+name+'_C'),name+' import failed'

kind=unreal.load_class(None,'/Game/DasRogue/Pickups/BP_HealthPickupInteract.BP_HealthPickupInteract_C')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
pickup=next((a for a in actors.get_all_level_actors() if a.get_class()==kind),None)
if not pickup:pickup=actors.spawn_actor_from_class(kind,unreal.Vector(300,-250,80))
pickup.set_actor_label('Health pickup - press E - respawns in 5 seconds')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
print('DAS_HEALTH_PICKUP_PREPARE PASS')
