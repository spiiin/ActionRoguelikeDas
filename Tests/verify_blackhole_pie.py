"""Native continuous force, object-channel filtering, overlap destruction and lifespan."""
from pathlib import Path
import json,time,traceback
import unreal

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
actors={a.get_actor_label():a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)}
probe=actors['Blackhole probe']
near=actors['Blackhole near body'];far=actors['Blackhole far body']
pawn_body=actors['Blackhole Pawn channel body']
disabled=actors['Blackhole overlap disabled body'];static=actors['Blackhole nonsimulated body']
teardown_body=actors['Blackhole teardown body'].static_mesh_component
kind=unreal.load_class(None,'/Game/DasRogue/Projectiles/BP_RogueProjectileBlackhole.BP_RogueProjectileBlackhole_C')
center=unreal.Vector(7000,-2000,200)
result=Path(unreal.Paths.project_saved_dir())/'Tests/rogue_blackhole_pie.json'
s={'phase':'setup','at':unreal.GameplayStatics.get_time_seconds(world),'started':time.perf_counter(),'done':False,'checks':[]}
def live(obj):
    try:return unreal.SystemLibrary.is_valid(obj)
    except TypeError as error:
        if isinstance(obj,unreal.Object) and 'NativizeObject: Cannot nativize' in str(error):return False
        raise
def prop(obj,name):return obj.get_editor_property(name)
def now():return unreal.GameplayStatics.get_time_seconds(world)
def phase(name):s.update(phase=name,at=now())
def finish(error=None):
    s['done']=True;unreal.unregister_slate_post_tick_callback(s['handle'])
    result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks']},indent=2))
def tick(delta):
    if s['done'] or s.get('busy'):return
    s['busy']=True
    try:
        assert time.perf_counter()-s['started']<35,s['phase']
        for actor in [probe,s.get('hole'),s.get('moving')]:
            if actor is not None and live(actor):assert not prop(actor,'LastDasError'),prop(actor,'LastDasError')
        age=now()-s['at'];state=s['phase']
        if state=='setup':
            teardown_body.set_simulate_physics(False)
            probe.call_method('UsePawnChannel',args=(pawn_body,))
            s['far_origin']=far.get_actor_location();s['pawn_origin']=pawn_body.get_actor_location()
            hole=probe.call_method('Spawn',args=(kind,center,True));assert hole
            s['hole']=hole;s['born']=now()
            radial=prop(hole,'RadialForceComponent');sphere=prop(hole,'SphereComponent')
            assert prop(hole,'InitialSpeed')==500 and prop(hole,'CollisionRadius')==20
            assert hole.get_life_span()>4.8 and prop(radial,'radius')==1200 and prop(radial,'force_strength')==-800000
            assert radial.is_active() and str(sphere.get_collision_profile_name())=='BlackholeCore'
            assert not prop(hole,'HasImpacted') and prop(hole,'ImpactCount')==0
            s['checks'].append('inherited_projectile_uses_course_defaults_and_nonblocking_profile')
            disabled.static_mesh_component.set_simulate_physics(True)
            phase('pull');return
        if state=='pull':
            if age<.05:return
            assert live(near) and near.static_mesh_component.get_physics_linear_velocity().x< -20
            assert (pawn_body.get_actor_location()-s['pawn_origin']).length()<1
            assert (far.get_actor_location()-s['far_origin']).length()<1
            assert live(disabled)
            s['checks'].append('continuous_force_pulls_physics_bodies_but_excludes_Pawn_and_outside_radius')
            near.set_actor_location(center,False,True)
            near.static_mesh_component.set_physics_linear_velocity(unreal.Vector())
            phase('consume');return
        if state=='consume':
            if live(near):assert age<2,'Near body never reached core';return
            assert prop(s['hole'],'ConsumedActors')==1
            assert live(disabled), 'GenerateOverlapEvents=false body was consumed'
            s['checks'].append('native_core_overlap_consumes_actor_once_and_requires_overlap_events')
            probe.call_method('SetOverlap',args=(disabled,True))
            phase('enable');return
        if state=='enable':
            if live(disabled):assert age<1;return
            assert prop(s['hole'],'ConsumedActors')==2
            static.set_actor_location(center,False,True)
            phase('static');return
        if state=='static':
            if age<.2:return
            assert live(static) and prop(s['hole'],'ConsumedActors')==2
            assert prop(s['hole'],'ImpactCount')==0
            s['checks'].append('overlapping_nonsimulated_PhysicsBody_is_preserved')
            static.set_actor_location(unreal.Vector(7000,-1000,200),False,True)
            phase('expiry');return
        if state=='expiry':
            if live(s['hole']):assert now()-s['born']<5.6;return
            assert 4.8<=now()-s['born']<5.6
            s['checks'].append('native_five_second_lifespan_removes_core_and_force')
            moving=probe.call_method('Spawn',args=(kind,unreal.Vector(10000,-2000,200),False));assert moving
            s['moving']=moving;s['moving_origin']=moving.get_actor_location();phase('moving');return
        if state=='moving':
            if age<.8:return
            moving=s['moving'];delta_position=moving.get_actor_location()-s['moving_origin']
            assert 350<delta_position.x<450 and abs(delta_position.y)<1
            assert prop(moving,'ImpactCount')==0 and not prop(moving,'HasImpacted')
            s['checks'].append('500cm_per_second_projectile_passes_through_world_wall_without_base_impact')
            teardown_body.set_simulate_physics(True)
            phase('active_force');return
        if state=='active_force':
            if age<.05:return
            assert teardown_body.get_physics_linear_velocity().y< -20
            s['moving'].destroy_actor();phase('drain');return
        if state=='drain':
            if age<.1:return
            teardown_body.set_physics_linear_velocity(unreal.Vector())
            phase('stopped');return
        if state=='stopped':
            if age<.2:return
            assert teardown_body.get_physics_linear_velocity().length()<1
            assert live(pawn_body) and live(far)
            s['checks'].append('destroying_active_projectile_stops_native_force_without_late_callbacks')
            wall=probe.call_method('Spawn',args=(unreal.StaticMeshActor,unreal.Vector(11300,-2000,200),False))
            wall.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
            wall.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
            wall.static_mesh_component.set_collision_profile_name('BlockAll')
            wall.set_actor_scale3d(unreal.Vector(.2,5,5))
            base_kind=unreal.load_class(None,'/Game/DasRogue/BP_RogueProjectile.BP_RogueProjectile_C')
            s['base']=probe.call_method('Spawn',args=(base_kind,unreal.Vector(11000,-2000,200),False))
            phase('base_profile');return
        if state=='base_profile':
            if age<.035:return
            base=s['base'];assert live(base)
            assert prop(base,'InitialSpeed')==2000 and prop(base,'CollisionProfile')=='Projectile'
            assert str(prop(base,'SphereComponent').get_collision_profile_name())=='Projectile'
            assert base.get_life_span()>29
            phase('base_hit');return
        if state=='base_hit':
            if live(s['base']):assert age<1,'Base projectile stopped colliding';return
            s['checks'].append('base_projectile_retains_2000_speed_30_second_lifespan_and_wall_collision')
            finish()
    except Exception:finish(traceback.format_exc())
    finally:s['busy']=False
s['handle']=unreal.register_slate_post_tick_callback(tick)
