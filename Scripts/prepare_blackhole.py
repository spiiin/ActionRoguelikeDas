"""Prepare a separate physics arena; attraction and consumption execute in DAS."""
from pathlib import Path
import runpy
import unreal

runpy.run_path(str(Path(__file__).parent/'prepare_character.py'))
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world=editor.get_editor_world()
for source,path,identity in [
    ('rogue_projectile','/Game/DasRogue/BP_RogueProjectile','rogue.RogueProjectile'),
    ('rogue_projectile_blackhole','/Game/DasRogue/Projectiles/BP_RogueProjectileBlackhole','rogue.RogueProjectileBlackhole'),
    ('rogue_blackhole_demo','/Game/DasRogue/Projectiles/BP_BlackholeDemo','roguedemo.RogueBlackholeDemo'),
    ('rogue_blackhole_probe','/Game/DasRogue/Tests/BP_RogueBlackholeProbe','roguetest.RogueBlackholeProbe')]:
    unreal.SystemLibrary.execute_console_command(world,f'Das.DSL.Apply {source}.das {path} {identity}')
    name=path.rsplit('/',1)[-1]
    assert unreal.load_class(None,path+'.'+name+'_C'),identity
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem) or unreal.get_default_object(unreal.LevelEditorSubsystem)
map_path='/Game/DasRogue/Maps/BlackholeTest'
if world.get_name()!='BlackholeTest':
    if unreal.get_editor_subsystem(unreal.EditorAssetSubsystem).does_asset_exist(map_path):assert level.load_level(map_path)
    else:assert level.new_level_from_template(map_path,'/Game/DasRogue/Maps/BarrelTest')
world=editor.get_editor_world()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in list(actors.get_all_level_actors()):
    name=actor.get_class().get_name()
    if name.startswith('BP_') and name not in ('BP_BlackholeDemo_C','BP_RogueBlackholeProbe_C'):
        actors.destroy_actor(actor)
    elif actor.get_actor_label().startswith('Barrel '):actors.destroy_actor(actor)
existing={a.get_actor_label():a for a in actors.get_all_level_actors()}
def make(label,kind,location):
    actor=existing.get(label) or actors.spawn_actor_from_class(kind,location)
    actor.set_actor_label(label);actor.set_actor_location(location,False,True)
    return actor
cube=unreal.load_asset('/Engine/BasicShapes/Cube')
floor=make('Blackhole arena floor',unreal.StaticMeshActor,unreal.Vector(7500,-2000,-50))
floor.static_mesh_component.set_static_mesh(cube);floor.set_actor_scale3d(unreal.Vector(85,25,1))
demo=unreal.load_class(None,'/Game/DasRogue/Projectiles/BP_BlackholeDemo.BP_BlackholeDemo_C')
probe=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueBlackholeProbe.BP_RogueBlackholeProbe_C')
make('Blackhole demo - stationary - 5 seconds',demo,unreal.Vector(4000,-2000,200))
make('Blackhole probe',probe,unreal.Vector(7000,-2800,200))
for label,position,sim in [
    ('Blackhole demo cube A',unreal.Vector(4400,-2000,200),True),
    ('Blackhole demo cube B',unreal.Vector(4000,-2500,200),True),
    ('Blackhole near body',unreal.Vector(7600,-2000,200),True),
    ('Blackhole far body',unreal.Vector(8500,-2000,200),True),
    ('Blackhole Pawn channel body',unreal.Vector(7000,-2600,200),True),
    ('Blackhole overlap disabled body',unreal.Vector(7000,-2000,200),False),
    ('Blackhole nonsimulated body',unreal.Vector(7000,-1000,200),False),
    ('Blackhole teardown body',unreal.Vector(10000,-1400,200),True)]:
    actor=make(label,unreal.StaticMeshActor,position)
    mesh=actor.static_mesh_component
    mesh.set_mobility(unreal.ComponentMobility.MOVABLE);mesh.set_static_mesh(cube)
    actor.set_actor_scale3d(unreal.Vector(.3,.3,.3))
    mesh.set_collision_profile_name('PhysicsActor');mesh.set_enable_gravity(False)
    mesh.set_editor_property('generate_overlap_events',label!='Blackhole overlap disabled body')
    mesh.set_simulate_physics(sim)
wall=make('Blackhole ignored wall',unreal.StaticMeshActor,unreal.Vector(10300,-2000,200))
wall.static_mesh_component.set_static_mesh(cube);wall.set_actor_scale3d(unreal.Vector(.2,5,5))
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
print('DAS_BLACKHOLE_PREPARED')
