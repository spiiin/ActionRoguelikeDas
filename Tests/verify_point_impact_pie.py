"""Verify native point-damage delivery and physics from real daScript projectiles."""
import json
import time
import traceback
from pathlib import Path
import unreal

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
target_class=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RoguePointDamageTarget.BP_RoguePointDamageTarget_C')
projectile_class=unreal.load_class(None,'/Game/DasRogue/BP_MagicProjectileDemo.BP_MagicProjectileDemo_C')
assert target_class and projectile_class
result=Path(__file__).resolve().parents[1]/'Saved/Tests/rogue_point_impact_pie.json'
s={'done':False,'phase':'point','started':time.perf_counter(),'at':unreal.GameplayStatics.get_time_seconds(world),'checks':[],'actors':[]}

def spawn(kind,location):
    actor=probe.call_method('Spawn',args=(kind,location,unreal.Rotator()))
    assert actor
    s['actors'].append(actor)
    return actor

def shot(target,damage=25,impulse=200000):
    actor=spawn(projectile_class,target.get_actor_location()+unreal.Vector(-220,0,0))
    actor.set_editor_property('AttackDamage',damage)
    actor.set_editor_property('ImpulseIntensity',impulse)
    actor.set_editor_property('instigator',pawn)
    return actor

def phase(name):s['phase']=name;s['at']=unreal.GameplayStatics.get_time_seconds(world)

def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    for actor in s['actors']:
        if unreal.SystemLibrary.is_valid(actor):actor.destroy_actor()
    result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks']},indent=2))

target=spawn(target_class,unreal.Vector(2000,2000,250))
s['shot']=shot(target)

def cube(location):
    actor=spawn(unreal.StaticMeshActor,location)
    mesh=actor.static_mesh_component
    mesh.set_mobility(unreal.ComponentMobility.MOVABLE)
    mesh.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube.Cube'))
    mesh.set_collision_profile_name('PhysicsActor')
    mesh.set_enable_gravity(False)
    mesh.set_simulate_physics(True)
    return actor

def tick(delta):
    if s['done']:return
    try:
        assert time.perf_counter()-s['started']<45,'Point impact timeout'
        age=unreal.GameplayStatics.get_time_seconds(world)-s['at']
        if age<.3:return
        name=s['phase']
        if name=='point':
            assert not target.get_editor_property('LastDasError'),target.get_editor_property('LastDasError')
            assert target.get_editor_property('PointHits')==1,target.get_editor_property('PointHits')
            assert target.get_editor_property('PointDamage')==25
            assert target.get_editor_property('Attributes').get_editor_property('Health')==75
            assert target.get_editor_property('HitComponent')==target.get_editor_property('Visual')
            direction=target.get_editor_property('ShotDirection')
            assert direction.x>.99 and abs(direction.y)<.01 and abs(direction.z)<.01,str(direction)
            location=target.get_editor_property('HitLocation')
            assert 1940<location.x<2000 and abs(location.y-2000)<1,str(location)
            assert target.get_editor_property('DamageController')==pawn.get_controller()
            assert not unreal.SystemLibrary.is_valid(s['shot']),'Projectile should be destroyed after damage delivery'
            s['checks'].append({'point_damage_once':True,'health_damage_once':True,'hit_component_location_direction':True,'controller_preserved':True})
            s['cube']=cube(unreal.Vector(2000,2400,250));s['origin']=s['cube'].get_actor_location()
            s['shot']=shot(s['cube'])
            phase('physics');return
        if name=='physics':
            mesh=s['cube'].static_mesh_component
            velocity=mesh.get_physics_linear_velocity()
            assert velocity.x>1,str(velocity)
            assert s['cube'].get_actor_location().x>s['origin'].x+1
            assert not unreal.SystemLibrary.is_valid(s['shot'])
            s['checks'].append({'simulating_body_receives_impulse':True,'projectile_destroyed':True})
            s['zero']=cube(unreal.Vector(2000,2800,250));s['origin']=s['zero'].get_actor_location()
            s['shot']=shot(s['zero'],damage=0,impulse=0)
            phase('zero');return
        if name=='zero':
            velocity=s['zero'].static_mesh_component.get_physics_linear_velocity()
            assert abs(velocity.x)<.1 and abs(velocity.y)<.1 and abs(velocity.z)<.1,str(velocity)
            assert not unreal.SystemLibrary.is_valid(s['shot'])
            assert target.get_editor_property('PointHits')==1
            s['checks'].append({'zero_impulse_body_stays_still':True,'zero_damage_impact_consumed':True,'static_target_no_physics_error':True})
            finish()
    except Exception:finish(traceback.format_exc())

s['handle']=unreal.register_slate_post_tick_callback(tick)
