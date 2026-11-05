from pathlib import Path
import unreal,runpy
root=Path(__file__).resolve().parents[1]
runpy.run_path(str(root/'Scripts/prepare_course_effects.py'))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label() in ['Course effects test probe','Teleport effect test wall']:
        actors.destroy_actor(actor)
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_teleport_probe.das /Game/DasRogue/Tests/BP_RogueTeleportProbe roguetest.RogueTeleportProbe')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
probe=actors.spawn_actor_from_class(unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueTeleportProbe.BP_RogueTeleportProbe_C'),unreal.Vector())
probe.set_actor_label('Course effects test probe')
wall=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(20000,0,1000))
wall.set_actor_label('Teleport effect test wall')
wall.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
wall.static_mesh_component.set_collision_profile_name('BlockAll')
wall.set_actor_scale3d(unreal.Vector(1,10,10))
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
