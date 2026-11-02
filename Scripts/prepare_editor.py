import unreal
from pathlib import Path

ROOT=Path(r"C:/src/ActionRoguelikeDas")
MAP="/Game/DasRogue/Maps/ChestTest"
editor=unreal.EditorLoadingAndSavingUtils
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for command in [
    "Das.DSL.Interfaces.Apply rogue_interaction_interface.das /Game/DasRogue/Types",
    "Das.DSL.Apply rogue_item_chest.das /Game/DasRogue/BP_RogueItemChest rogue.RogueItemChest",
    "Das.DSL.Apply rogue_chest_demo.das /Game/DasRogue/BP_ChestDemo roguedemo.RogueChestDemo",
]:
    unreal.SystemLibrary.execute_console_command(world,command)
cls=unreal.load_class(None,"/Game/DasRogue/BP_ChestDemo.BP_ChestDemo_C")
if not cls:
    raise RuntimeError("Cannot import daScript chest demo; inspect DAS_DSL errors")
if (ROOT/"Content/DasRogue/Maps/ChestTest.umap").exists():
    world=editor.load_map(MAP)
else:
    world=editor.new_blank_map(False)
    cube=unreal.load_asset("/Engine/BasicShapes/Cube")
    floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,-30))
    floor.set_actor_label("Test floor")
    floor.static_mesh_component.set_static_mesh(cube)
    floor.set_actor_scale3d(unreal.Vector(12,12,0.3))
    chest=actors.spawn_actor_from_class(cls,unreal.Vector(0,0,60))
    chest.set_actor_label("daScript Chest - opens 1 second after Play")
    base=chest.get_editor_property("BaseMeshComponent")
    lid=chest.get_editor_property("LidMeshComponent")
    base.set_static_mesh(cube)
    lid.set_static_mesh(cube)
    # Keep root scale at identity; use separate component dimensions.
    base.set_relative_scale3d(unreal.Vector(2,1.3,1))
    lid.set_relative_location(unreal.Vector(0,0,60),False,True)
    lid.set_relative_scale3d(unreal.Vector(1.025,1.04,0.15))
    # Lid inherits root dimensions. The simple cube cover uses its centre pivot.
    light=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,500),unreal.Rotator(-45,-30,0))
    light.light_component.set_editor_property("mobility",unreal.ComponentMobility.MOVABLE)
    light.light_component.set_editor_property("intensity",5.0)
    actors.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector(0,0,0))
    actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,300))
    camera_position=unreal.Vector(500,-600,350)
    camera_rotation=unreal.MathLibrary.find_look_at_rotation(camera_position,unreal.Vector(0,0,85))
    actors.spawn_actor_from_class(unreal.PlayerStart,camera_position,camera_rotation)
    editor.save_map(world,MAP)
    actors.set_selected_level_actors([chest])
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(
    unreal.Vector(500,-600,350),unreal.MathLibrary.find_look_at_rotation(unreal.Vector(500,-600,350),unreal.Vector(0,0,85)))
editor.save_map(world,MAP)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
(ROOT/"Saved").mkdir(exist_ok=True)
(ROOT/"Saved/editor-ready.txt").write_text("Map ready: "+MAP,encoding="utf-8")
unreal.log("DAS_ROGUE_EDITOR_READY map="+MAP)


