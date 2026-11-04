from pathlib import Path
import runpy
import unreal
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in list(actors.get_all_level_actors()):
    if (actor.get_class().get_name()=='BP_RogueTeleportProbe_C' or
        actor.get_actor_label()=='Teleport impact test wall' or
        actor.get_actor_label().startswith('Teleport blocked destination')):
        actors.destroy_actor(actor)
runpy.run_path(str(Path(__file__).with_name('prepare_additional_attacks.py')))
kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueTeleportProbe.BP_RogueTeleportProbe_C')
assert actors.spawn_actor_from_class(kind,unreal.Vector(0,0,-1000))
for label,position,scale in [
    ('Teleport impact test wall',unreal.Vector(20500,0,1000),unreal.Vector(1,5,5)),
    # Opposite penetration vectors cancel, so FindTeleportSpot cannot find a
    # safe adjustment. A single box permits successful native de-penetration.
    ('Teleport blocked destination',unreal.Vector(24990,0,1000),unreal.Vector(20,40,40)),
    ('Teleport blocked destination opposite',unreal.Vector(25010,0,1000),unreal.Vector(20,40,40)),
]:
    actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,position)
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    actor.set_actor_scale3d(scale)
