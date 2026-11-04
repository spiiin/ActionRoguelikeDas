"""Actual native movement against the pinned original Blueprint settings."""
import json, math, time, traceback
from pathlib import Path
import unreal

root=Path(__file__).resolve().parents[1]
reference=json.loads((root/'Saved/Tests/original_movement_reference.json').read_text())['blueprint']
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
p=unreal.GameplayStatics.get_player_pawn(w,0)
pc=unreal.GameplayStatics.get_player_controller(w,0)
m=p.get_editor_property('character_movement')
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
inputs=max((v for v in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if v.get_outer().get_class().get_name()=='LocalPlayer'),key=lambda v:int(v.get_outer().get_name().rsplit('_',1)[-1]))
move=unreal.load_asset('/Game/DasRogue/Input/IA_Move')
sprint=unreal.load_asset('/Game/DasRogue/Input/IA_Sprint')
floor=probe.call_method('Spawn',args=(unreal.StaticMeshActor.static_class(),unreal.Vector(0,-4000,-50),unreal.Rotator()))
assert floor
floor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
floor.set_actor_scale3d(unreal.Vector(60,60,1))
floor.static_mesh_component.set_collision_profile_name('BlockAll')
cases=[(yaw,forward,right) for yaw in (0,90) for forward,right in ((1,0),(-1,0),(0,1),(0,-1))]
s={'phase':'settings','index':0,'at':0,'started':time.perf_counter(),'checks':[],'done':False,'samples':[]}

def now():return unreal.GameplayStatics.get_time_seconds(w)
def phase(name):s['phase']=name;s['at']=now()
def near(a,b,tolerance=.01):assert abs(a-b)<=tolerance,(a,b)
def yaw_error(a,b):return abs((a-b+180)%360-180)
def reset():
    m.stop_movement_immediately()
    p.set_actor_location(unreal.Vector(0,-4000,160),False,True)
    p.set_actor_rotation(unreal.Rotator(),False)
    pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=cases[s['index']][0],roll=0))
    phase('settle')
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    m.stop_movement_immediately()
    if unreal.SystemLibrary.is_valid(floor):floor.destroy_actor()
    (root/'Saved/Tests/rogue_movement_pie.json').write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks'],'samples':s['samples'],'reference':reference,'elapsed_seconds':time.perf_counter()-s['started']},indent=2),encoding='utf-8')

def tick(delta):
    if s['done']:return
    try:
        assert time.perf_counter()-s['started']<60,s['phase']
        for obj in (p,pc):assert not obj.get_editor_property('LastDasError'),obj.get_editor_property('LastDasError')
        age=now()-s['at']
        if s['phase']=='settings':
            for key,value in reference['actor'].items():
                assert p.get_editor_property(key)==value,(key,p.get_editor_property(key),value)
            for key in ['orient_rotation_to_movement','use_controller_desired_rotation','max_acceleration',
                'braking_deceleration_walking','ground_friction','braking_friction_factor','use_separate_braking_friction',
                'braking_friction','jump_z_velocity','air_control','gravity_scale']:
                expected=reference['movement'][key]
                assert not isinstance(expected,dict),(key,expected)
                near(float(m.get_editor_property(key)),float(expected))
            rate=m.get_editor_property('rotation_rate')
            for key,value in reference['movement']['rotation_rate'].items():near(getattr(rate,key),value)
            arm=p.get_editor_property('SpringArmComponent')
            near(arm.get_editor_property('target_arm_length'),reference['SpringArmComponent']['target_arm_length'])
            location=arm.get_editor_property('relative_location')
            for key,value in reference['SpringArmComponent']['relative_location'].items():near(getattr(location,key),value)
            for key in ['socket_offset','target_offset']:
                value=arm.get_editor_property(key)
                for axis,expected in reference['SpringArmComponent'][key].items():near(getattr(value,axis),expected)
            for key in ['enable_camera_lag','enable_camera_rotation_lag','do_collision_test','probe_size']:
                near(float(arm.get_editor_property(key)),float(reference['SpringArmComponent'][key]))
            near(p.get_editor_property('CameraComponent').get_editor_property('field_of_view'),reference['CameraComponent']['field_of_view'])
            attrs=reference['ActionSystemComponent']
            # Modifier is Transient and protected in the original USTRUCT; CDO values start at zero.
            speed=attrs['MoveSpeed']['Base']*attrs['MoveSpeedMultiplier']['Base']
            near(m.get_editor_property('max_walk_speed'),speed)
            s['speed']=speed
            s['checks'].append('rotation_acceleration_braking_jump_air_and_attribute_speed_match_original_blueprint')
            reset();return
        if s['phase']=='settle':
            if age<.5:return
            s['origin']=p.get_actor_location()
            phase('move');return
        if s['phase']=='move':
            yaw,forward,right=cases[s['index']]
            inputs.inject_input_vector_for_action(move,unreal.Vector(forward,right,0),[],[])
            if age<.9:return
            radians=math.radians(yaw)
            dx=forward*math.cos(radians)-right*math.sin(radians)
            dy=forward*math.sin(radians)+right*math.cos(radians)
            velocity=p.get_velocity()
            speed=math.hypot(velocity.x,velocity.y)
            near(speed,s['speed'],2.0)
            assert (velocity.x*dx+velocity.y*dy)/speed>.99,(yaw,forward,right,velocity)
            displacement=p.get_actor_location()-s['origin']
            assert displacement.x*dx+displacement.y*dy>100,displacement
            facing=yaw if reference['actor']['use_controller_rotation_yaw'] or reference['movement']['use_controller_desired_rotation'] else (math.degrees(math.atan2(dy,dx)) if reference['movement']['orient_rotation_to_movement'] else 0)
            assert yaw_error(p.get_actor_rotation().yaw,facing)<5,(p.get_actor_rotation(),facing)
            s['samples'].append({'camera_yaw':yaw,'forward':forward,'right':right,'speed':speed,'actor_yaw':p.get_actor_rotation().yaw,'expected_actor_yaw':facing})
            s['checks'].append(f'native_direction_speed_and_facing_yaw_{yaw}_input_{forward}_{right}')
            phase('stop');return
        if s['phase']=='stop':
            if age<.4:return
            velocity=p.get_velocity();assert math.hypot(velocity.x,velocity.y)<1,velocity
            s['index']+=1
            if s['index']<len(cases):reset()
            else:
                s['checks'].append('release_brakes_to_rest_after_every_direction')
                p.set_actor_location(unreal.Vector(0,-4000,160),False,True)
                pc.set_control_rotation(unreal.Rotator())
                phase('sprint')
            return
        if s['phase']=='sprint':
            inputs.inject_input_vector_for_action(move,unreal.Vector(1,0,0),[],[])
            inputs.inject_input_vector_for_action(sprint,unreal.Vector(1,0,0),[],[])
            if age<1.2:return
            near(m.get_editor_property('max_walk_speed'),880)
            velocity=p.get_velocity();near(math.hypot(velocity.x,velocity.y),880,2.0)
            s['checks'].append('real_sprint_input_reaches_880_from_course_base_550')
            phase('sprint_release');return
        if s['phase']=='sprint_release':
            if age<.5:return
            near(m.get_editor_property('max_walk_speed'),550)
            velocity=p.get_velocity();assert math.hypot(velocity.x,velocity.y)<1,velocity
            s['checks'].append('sprint_release_restores_course_walk_speed_and_stops')
            finish()
    except Exception:finish(traceback.format_exc())
s['handle']=unreal.register_slate_post_tick_callback(tick)
