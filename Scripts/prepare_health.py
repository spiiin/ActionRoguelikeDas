import unreal
from pathlib import Path
__import__('runpy').run_path(str(Path(__file__).resolve().with_name('prepare_attribute_sets.py')))
ROOT=Path(r"C:/src/ActionRoguelikeDas")
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
__import__('runpy').run_path(str(Path(__file__).resolve().with_name('prepare_burning_effect.py')))
import unreal
assets=unreal.AssetToolsHelpers.get_asset_tools()
path='/Game/DasRogue/Materials/M_TargetHealth'
mat=unreal.load_asset(path)
if not mat:
    mat=assets.create_asset('M_TargetHealth','/Game/DasRogue/Materials',unreal.Material,unreal.MaterialFactoryNew())
    color=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionVectorParameter,0,0)
    color.set_editor_property('parameter_name','Color')
    color.set_editor_property('default_value',unreal.LinearColor(0.05,1.0,0.05,1.0))
    unreal.MaterialEditingLibrary.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat)

for command in [
    "Das.DSL.Interfaces.Apply rogue_projectile_impact_interface.das /Game/DasRogue/Types",
    "Das.DSL.Apply rogue_attribute_component.das /Game/DasRogue/BP_RogueAttributeComponent rogue.RogueAttributeComponent",
    "Das.DSL.Apply rogue_projectile.das /Game/DasRogue/BP_RogueProjectile rogue.RogueProjectile",
    "Das.DSL.Apply rogue_magic_projectile.das /Game/DasRogue/BP_RogueMagicProjectile rogue.RogueMagicProjectile",
    "Das.DSL.Apply rogue_magic_projectile_demo.das /Game/DasRogue/BP_MagicProjectileDemo roguedemo.RogueMagicProjectileDemo",
    "Das.DSL.Apply rogue_target_dummy.das /Game/DasRogue/BP_TargetDummy roguedemo.RogueTargetDummy",
    "Das.DSL.Apply rogue_player_controller.das /Game/DasRogue/BP_RoguePlayerController rogue.RoguePlayerController",
]:
    unreal.SystemLibrary.execute_console_command(world,command)
cls=unreal.load_class(None,"/Game/DasRogue/BP_TargetDummy.BP_TargetDummy_C")
assert cls,"Target import failed"
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
existing=[a for a in actors.get_all_level_actors() if a.get_class()==cls]
if not existing:
    target=actors.spawn_actor_from_class(cls,unreal.Vector(220,100,100))
    target.set_actor_label("daScript Target - 100 HP / 4 hits")
    target.get_editor_property("Label").set_relative_rotation(unreal.Rotator(pitch=0,yaw=-60,roll=0),False,True)
else:
    target=existing[0]
controller=unreal.load_class(None,"/Game/DasRogue/BP_RoguePlayerController.BP_RoguePlayerController_C")
expected=unreal.load_class(None,"/Game/DasRogue/BP_MagicProjectileDemo.BP_MagicProjectileDemo_C")
assert expected and unreal.get_default_object(controller).get_editor_property("ProjectileClass")==expected,"Controller default did not update"
print("target",target.get_actor_location())
assert unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
print("DAS_ROGUE_HEALTH_READY")
