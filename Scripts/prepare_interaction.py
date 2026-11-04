import unreal
from pathlib import Path

ROOT=Path(r"C:/src/ActionRoguelikeDas")
MAP="/Game/DasRogue/Maps/ChestTest"
saving=unreal.EditorLoadingAndSavingUtils
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world=saving.load_map(MAP)
if not world:
    raise RuntimeError("Prepare ChestTest before installing interaction")
# Input assets are editor configuration; all runtime selection and dispatch is daScript.
tools=unreal.AssetToolsHelpers.get_asset_tools()
def asset(name,cls,factory):
    path="/Game/DasRogue/Input/"+name
    value=unreal.load_asset(path)
    if not value:
        value=tools.create_asset(name,"/Game/DasRogue/Input",cls,factory())
    if not value:
        raise RuntimeError("Cannot create "+path)
    return value
action=asset("IA_Interact",unreal.InputAction,unreal.InputAction_Factory)
action.set_editor_property("value_type",unreal.InputActionValueType.BOOLEAN)
mapping=asset("IMC_Rogue",unreal.InputMappingContext,unreal.InputMappingContext_Factory)
mapping.modify(True)
mapping.unmap_all()
key=unreal.Key()
key.set_editor_property("key_name","E")
mapping.map_key(action,key)
fire=asset("IA_Fire",unreal.InputAction,unreal.InputAction_Factory)
fire.set_editor_property("value_type",unreal.InputActionValueType.BOOLEAN)
mouse=unreal.Key()
mouse.set_editor_property("key_name","LeftMouseButton")
mapping.map_key(fire,mouse)
additional=[]
for name,key_name in [('IA_SecondaryAttack','F'),('IA_SpecialAttack','Q')]:
    attack=asset(name,unreal.InputAction,unreal.InputAction_Factory)
    attack.set_editor_property('value_type',unreal.InputActionValueType.BOOLEAN)
    key=unreal.Key()
    key.set_editor_property('key_name',key_name)
    mapping.map_key(attack,key)
    additional.append(attack)
if not saving.save_packages([x.get_outer() for x in [mapping,action,fire,*additional]],False):
    raise RuntimeError("Cannot save input assets")

__import__('runpy').run_path(str(Path(__file__).resolve().with_name('prepare_burning_effect.py')))

for command in [
    "Das.DSL.Interfaces.Apply rogue_projectile_impact_interface.das /Game/DasRogue/Types",
    "Das.DSL.Interfaces.Apply rogue_interaction_interface.das /Game/DasRogue/Types",
    "Das.DSL.Apply rogue_item_chest.das /Game/DasRogue/BP_RogueItemChest rogue.RogueItemChest",
    "Das.DSL.Apply rogue_interaction_component.das /Game/DasRogue/BP_RogueInteractionComponent rogue.RogueInteractionComponent",
    "Das.DSL.Apply rogue_projectile.das /Game/DasRogue/BP_RogueProjectile rogue.RogueProjectile",
    "Das.DSL.Apply rogue_projectile_demo.das /Game/DasRogue/BP_ProjectileDemo roguedemo.RogueProjectileDemo",
    "Das.DSL.Apply rogue_magic_projectile.das /Game/DasRogue/BP_RogueMagicProjectile rogue.RogueMagicProjectile",
    "Das.DSL.Apply rogue_magic_projectile_demo.das /Game/DasRogue/BP_MagicProjectileDemo roguedemo.RogueMagicProjectileDemo",
    "Das.DSL.Apply rogue_player_controller.das /Game/DasRogue/BP_RoguePlayerController rogue.RoguePlayerController",
    "Das.DSL.Apply rogue_interactive_chest.das /Game/DasRogue/BP_InteractiveChest roguedemo.RogueInteractiveChest",
    "Das.DSL.Apply rogue_hinged_chest.das /Game/DasRogue/BP_InteractiveChestHinged roguedemo.RogueInteractiveChestHinged",
]:
    unreal.SystemLibrary.execute_console_command(world,command)
controller=unreal.load_class(None,"/Game/DasRogue/BP_RoguePlayerController.BP_RoguePlayerController_C")
chest_class=unreal.load_class(None,"/Game/DasRogue/BP_InteractiveChestHinged.BP_InteractiveChestHinged_C")
if not controller or not chest_class:
    raise RuntimeError("daScript interaction import failed")
cdo=unreal.get_default_object(controller)
cdo.set_editor_property("Controls",mapping)
cdo.set_editor_property("Input_Interact",action)
cdo.set_editor_property("TeamId",1)
if cdo.get_editor_property("Input_Fire") != fire:
    raise RuntimeError("Controller IA_Fire default is missing")
projectile=unreal.load_class(None,"/Game/DasRogue/BP_MagicProjectileDemo.BP_MagicProjectileDemo_C")
if not projectile or cdo.get_editor_property("ProjectileClass") != projectile:
    raise RuntimeError("Controller projectile class default is missing")
game=unreal.load_asset("/Game/DasRogue/BP_RogueGameMode")
if not game:
    factory=unreal.BlueprintFactory()
    factory.set_editor_property("parent_class",unreal.GameModeBase)
    game=tools.create_asset("BP_RogueGameMode","/Game/DasRogue",unreal.Blueprint,factory)
game_class=unreal.load_class(None,"/Game/DasRogue/BP_RogueGameMode.BP_RogueGameMode_C")
if not game_class:
    raise RuntimeError("Cannot configure Rogue GameMode")
unreal.get_default_object(game_class).set_editor_property("player_controller_class",controller)
game.modify(True)
if not unreal.BlueprintEditorLibrary.compile_blueprint(game):
    raise RuntimeError("Cannot compile Rogue GameMode")
game_class=unreal.load_class(None,"/Game/DasRogue/BP_RogueGameMode.BP_RogueGameMode_C")
if unreal.get_default_object(game_class).get_editor_property("player_controller_class") != controller:
    raise RuntimeError("GameMode did not retain the daScript controller")
world.get_world_settings().set_editor_property("default_game_mode",game_class)
# Replace only actors of the original generated auto-demo class; preserve their components/settings.
old_path="/Game/DasRogue/BP_ChestDemo.BP_ChestDemo_C"
for old in list(actors.get_all_level_actors()):
    if old.get_class().get_path_name() not in [old_path,"/Game/DasRogue/BP_InteractiveChest.BP_InteractiveChest_C"]:
        continue
    pose=old.get_actor_transform()
    new=actors.spawn_actor_from_class(chest_class,pose.translation,pose.rotation.rotator())
    new.set_actor_transform(pose,False,True)
    for name in ["BaseMeshComponent"]:
        source=old.get_editor_property(name)
        target=new.get_editor_property(name)
        target.set_static_mesh(source.get_editor_property("static_mesh"))
        target.set_relative_transform(source.get_relative_transform(),False,True)
    for name in ["AnimationSpeed","AnimationTargetPitch"]:
        new.set_editor_property(name,old.get_editor_property(name))
    new.set_actor_label("daScript Chest - press E")
    actors.destroy_actor(old)
    actors.set_selected_level_actors([new])
# Keep the cube demo's mesh offset from its rear-edge hinge.
exec((ROOT/"Scripts/configure_chest_geometry.py").read_text(encoding="utf-8"))
configure_chest_geometry(actors)
view=unreal.Vector(350,-450,220)
rotation=unreal.MathLibrary.find_look_at_rotation(view,unreal.Vector(0,0,85))
starts=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.PlayerStart)]
if starts:
    starts[0].set_actor_location(view,False,True)
    starts[0].set_actor_rotation(rotation,True)
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(view,rotation)
saving.save_map(world,MAP)
saving.save_dirty_packages(True,True)
(ROOT/"Saved/interaction-ready.txt").write_text("E interaction configured",encoding="utf-8")
unreal.log("DAS_ROGUE_INTERACTION_EDITOR_READY")
