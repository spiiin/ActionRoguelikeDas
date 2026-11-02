import unreal
import runpy
from pathlib import Path

ROOT=Path(r"C:/src/ActionRoguelikeDas")
runpy.run_path(str(ROOT/"Scripts/prepare_interaction.py"))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
targets=[a for a in actors.get_all_level_actors() if a.get_actor_label()=="Projectile target wall"]
wall=targets[0] if targets else actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(-200,400,250))
wall.set_actor_label("Projectile target wall")
wall.set_actor_scale3d(unreal.Vector(12,0.5,6))
mesh=wall.get_component_by_class(unreal.StaticMeshComponent)
mesh.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
mesh.set_collision_profile_name("BlockAll")
unreal.EditorLoadingAndSavingUtils.save_map(world,"/Game/DasRogue/Maps/ChestTest")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
(ROOT/"Saved/projectile-ready.txt").write_text("LMB shoots, E interacts",encoding="utf-8")
unreal.log("DAS_ROGUE_PROJECTILE_EDITOR_READY")
