"""Native damage -> DAS fuse -> radial physics impulse, without blast damage."""
from pathlib import Path
import json,time,traceback
import unreal

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
all_actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
by_label={actor.get_actor_label():actor for actor in all_actors}
barrel=by_label['Explosive barrel - shoot once - 3 second fuse']
probe=by_label['Barrel damage observer']
near=by_label['Barrel near physics cube'].static_mesh_component
far=by_label['Barrel far physics cube'].static_mesh_component
kind=barrel.get_class()
result=Path(unreal.Paths.project_saved_dir())/'Tests/rogue_barrels_pie.json'
s={'phase':'settle','at':unreal.GameplayStatics.get_time_seconds(world),'checks':[],'done':False,'started':time.perf_counter()}
def prop(obj,name):return obj.get_editor_property(name)
def now():return unreal.GameplayStatics.get_time_seconds(world)
def phase(value):s.update(phase=value,at=now())
def damage(target,value=1.0):return unreal.GameplayStatics.apply_damage(target,value,None,probe,None)
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks']},indent=2))
def tick(delta):
    if s['done'] or s.get('busy'):return
    s['busy']=True
    try:
        assert time.perf_counter()-s['started']<35,s['phase']
        for actor in [barrel,probe,*s.get('extras',[])]:
            if unreal.SystemLibrary.is_valid(actor):assert not prop(actor,'LastDasError'),prop(actor,'LastDasError')
        age=now()-s['at'];state=s['phase']
        if state=='settle':
            if age<.4:return
            mesh=prop(barrel,'MeshComponent');radial=prop(barrel,'RadialForceComponent')
            assert mesh.is_simulating_physics() and str(mesh.get_collision_profile_name())=='PhysicsActor'
            assert prop(radial,'radius')==750 and prop(radial,'impulse_strength')==150000
            assert not prop(radial,'auto_activate') and prop(radial,'ignore_owning_actor')
            assert not prop(barrel,'Burning') and not prop(barrel,'Exploded')
            s['checks'].append('course_physics_and_radial_defaults')
            s['origin']=barrel.get_actor_location();s['near']=near.get_world_location();s['far']=far.get_world_location()
            damage(barrel);phase('fuse');return
        if state=='fuse':
            assert not prop(barrel,'Exploded'),age
            if age<.3:return
            assert prop(barrel,'Burning') and prop(barrel,'FuseStarts')==1
            damage(barrel);damage(barrel)
            s['checks'].append('native_damage_arms_once_and_repeated_damage_keeps_original_fuse')
            s['armed_at']=s['at'];phase('waiting');return
        if state=='waiting':
            elapsed=now()-s['armed_at']
            if not prop(barrel,'Exploded'):
                assert elapsed<3.6
                if elapsed<2.5:assert (near.get_world_location()-s['near']).length()<1
                return
            assert 2.8<=elapsed<=3.6,elapsed
            assert prop(barrel,'Explosions')==1 and not prop(barrel,'Burning')
            s['checks'].append('three_second_owner_timer_explodes_once')
            phase('impulse');return
        if state=='impulse':
            if age<.2:return
            assert near.get_physics_linear_velocity().x>20
            assert (near.get_world_location()-s['near']).length()>5
            assert (far.get_world_location()-s['far']).length()<1
            mesh=prop(barrel,'MeshComponent')
            assert mesh.get_physics_linear_velocity().z>100
            assert mesh.get_physics_angular_velocity_in_degrees().length()>100
            assert prop(probe,'DamageNotifications')==0
            s['checks'].append('radial_impulse_moves_near_body_leaves_far_body_and_applies_no_damage')
            s['checks'].append('own_barrel_receives_upward_and_angular_velocity_changes')
            barrel.call_method('Explode');damage(barrel)
            assert prop(barrel,'Explosions')==1 and prop(barrel,'FuseStarts')==1
            s['checks'].append('direct_and_damage_reentry_cannot_repeat_explosion')
            extra=probe.call_method('Spawn',args=(kind,unreal.Vector(6200,-2000,80)))
            extra.set_editor_property('ExplosionDelay',.3)
            damage(extra)
            s['extras']=[extra];phase('destroy');return
        if state=='destroy':
            if age<.05:return
            extra=s['extras'][0]
            assert prop(extra,'Burning')
            extra.destroy_actor();s['extras']=[]
            phase('destroyed');return
        if state=='destroyed':
            if age<.5:return
            s['checks'].append('destroying_burning_owner_cancels_pending_callback')
            # A direct Blueprint call during the fuse cancels its scheduled explosion.
            extra=probe.call_method('Spawn',args=(kind,unreal.Vector(6200,-2000,80)))
            extra.set_editor_property('ExplosionDelay',.2)
            damage(extra);s['extras']=[extra];phase('direct');return
        if state=='direct':
            if age<.05:return
            s['extras'][0].call_method('Explode');phase('direct_wait');return
        if state=='direct_wait':
            if age<.4:return
            assert prop(s['extras'][0],'Explosions')==1
            s['checks'].append('manual_explosion_cancels_fuse_without_second_impulse')
            finish()
    except Exception:finish(traceback.format_exc())
    finally:s['busy']=False
s['handle']=unreal.register_slate_post_tick_callback(tick)
