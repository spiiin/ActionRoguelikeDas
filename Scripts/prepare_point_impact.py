"""Import the point-damage fixture and add a playable physics target."""
from pathlib import Path
import shutil
import unreal
root=Path(__file__).resolve().parents[1]
shutil.copyfile(root/'Tests/Das/rogue_point_damage_target.das',root/'Content/Das/Scripts/rogue_point_damage_target.das')
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_point_damage_target.das /Game/DasRogue/Tests/BP_RoguePointDamageTarget roguetest.RoguePointDamageTarget')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
label='Physics target - shoot with LMB'
cube=next((a for a in actors.get_all_level_actors() if a.get_actor_label()==label),None)
if not cube:
    cube=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(120,-100,90))
    cube.set_actor_label(label)
    cube.set_actor_scale3d(unreal.Vector(.7,.7,.7))
    mesh=cube.static_mesh_component
    mesh.set_mobility(unreal.ComponentMobility.MOVABLE)
    mesh.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube.Cube'))
    mesh.set_collision_profile_name('PhysicsActor')
    mesh.set_simulate_physics(True)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
