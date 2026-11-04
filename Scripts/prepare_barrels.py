"""Assemble the barrel arena from engine assets; behavior lives in DAS."""
from pathlib import Path
import runpy
import unreal

runpy.run_path(str(Path(__file__).parent / "prepare_character.py"))

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for source,name,identity in [
    ('rogue_explosive_barrel','BP_RogueExplosiveBarrel','rogue.RogueExplosiveBarrel'),
    ('rogue_barrel_probe','BP_RogueBarrelProbe','roguetest.RogueBarrelProbe')]:
    folder='World' if source=='rogue_explosive_barrel' else 'Tests'
    path='/Game/DasRogue/'+folder+'/'+name
    unreal.SystemLibrary.execute_console_command(world,f'Das.DSL.Apply {source}.das {path} {identity}')
    assert unreal.load_class(None,path+'.'+name+'_C'),identity
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
print('DAS_BARRELS_PREPARE PASS')

level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem) or unreal.get_default_object(unreal.LevelEditorSubsystem)
map_path='/Game/DasRogue/Maps/BarrelTest'
if world.get_name()!='BarrelTest':
    if unreal.get_editor_subsystem(unreal.EditorAssetSubsystem).does_asset_exist(map_path):
        assert level.load_level(map_path)
    else:
        assert level.new_level_from_template(map_path,'/Game/DasRogue/Maps/ChestTest')
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
player_attributes=unreal.load_class(None,"/Game/DasRogue/Attributes/BP_RoguePlayerAttributeSet.BP_RoguePlayerAttributeSet_C")
assert player_attributes,"Prepare player attributes before the barrel arena"
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in list(actors.get_all_level_actors()):
    name=actor.get_class().get_name()
    if name.startswith('BP_') and name not in ('BP_RogueExplosiveBarrel_C','BP_RogueBarrelProbe_C'):
        actors.destroy_actor(actor)
    elif isinstance(actor,unreal.PlayerStart):
        actor.set_actor_location(unreal.Vector(4000,-2700,110),False,True)
        actor.set_actor_rotation(unreal.Rotator(0,90,0),False)

base=unreal.Vector(4000,-2000,80)
cube=unreal.load_asset('/Engine/BasicShapes/Cube')
existing={actor.get_actor_label():actor for actor in actors.get_all_level_actors()}
def make(label,kind,location):
    actor=existing.get(label) or actors.spawn_actor_from_class(kind,location)
    actor.set_actor_label(label)
    actor.set_actor_location(location,False,True)
    return actor
floor=make('Barrel arena floor',unreal.StaticMeshActor,unreal.Vector(4400,-2000,-50))
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_scale3d(unreal.Vector(25,20,1))
barrel_kind=unreal.load_class(None,'/Game/DasRogue/World/BP_RogueExplosiveBarrel.BP_RogueExplosiveBarrel_C')
probe_kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueBarrelProbe.BP_RogueBarrelProbe_C')
make('Explosive barrel - shoot once - 3 second fuse',barrel_kind,base)
make('Barrel damage observer',probe_kind,base+unreal.Vector(0,300,0))
for label,offset in [('Barrel near physics cube',300),('Barrel far physics cube',1000)]:
    actor=make(label,unreal.StaticMeshActor,base+unreal.Vector(offset,0,0))
    mesh=actor.static_mesh_component
    mesh.set_mobility(unreal.ComponentMobility.MOVABLE)
    mesh.set_static_mesh(cube)
    actor.set_actor_scale3d(unreal.Vector(.4,.4,.4))
    mesh.set_collision_profile_name('PhysicsActor')
    mesh.set_enable_gravity(False)
    mesh.set_simulate_physics(True)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
