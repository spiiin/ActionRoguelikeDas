"""Run in fresh ChestTest PIE. Native Enhanced Input, movement and camera updates."""
import unreal, time, json, math, traceback
from pathlib import Path
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert w
p=unreal.GameplayStatics.get_player_pawn(w,0)
pc=unreal.GameplayStatics.get_player_controller(w,0)
attack=next(a for a in p.get_editor_property('ActionSystem').get_editor_property('Actions') if a.get_class().get_name()=='BP_RogueActionProjectileAttack_C')
assert p.get_class().get_name()=='BP_RogueCharacter_C'
assert p.get_editor_property('ControlsBound')
movement=p.get_editor_property('character_movement')
boom=p.get_editor_property('SpringArmComponent')
camera=p.get_editor_property('CameraComponent')
assert camera.get_attach_parent()==boom
assert str(camera.get_attach_socket_name())=='SpringEndpoint'
assert boom.get_editor_property('target_arm_length')==350.0
assert boom.get_editor_property('use_pawn_control_rotation')
assert movement.get_editor_property('max_walk_speed')==450.0
entries=unreal.load_asset('/Game/DasRogue/Input/IMC_Character').get_editor_property('default_key_mappings').get_editor_property('mappings')
mappings={str(e.get_editor_property('key').get_editor_property('key_name')):e for e in entries}
subsystems=[s for s in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if s.get_outer().get_class().get_name()=='LocalPlayer']
def index(s):
    try:return int(s.get_outer().get_name().rsplit('_',1)[-1])
    except ValueError:return -1
inputs=max(subsystems,key=index)
def inject_key(name):
    e=mappings[name]
    inputs.inject_input_vector_for_action(e.get_editor_property('action'),unreal.Vector(1,0,0),e.get_editor_property('modifiers'),[])
def inject_action(name):
    inputs.inject_input_vector_for_action(unreal.load_asset('/Game/DasRogue/Input/'+name),unreal.Vector(1,0,0),[],[])
old_idle=unreal.SystemLibrary.get_console_variable_int_value('t.IdleWhenNotForeground')
unreal.SystemLibrary.execute_console_command(w,'t.IdleWhenNotForeground 0')
path=Path('C:/src/ActionRoguelikeDas/Saved/Tests/rogue_character_pie.json')
path.parent.mkdir(parents=True,exist_ok=True)
cases=[('W',0,1,0),('S',0,-1,0),('D',0,0,1),('A',0,0,-1),('W',90,0,1),('S',90,0,-1)]
s={'phase':'setup','case':0,'at':time.perf_counter(),'start':time.perf_counter(),'checks':[],'done':False}
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    unreal.SystemLibrary.execute_console_command(w,'t.IdleWhenNotForeground '+str(old_idle))
    result={'passed':error is None,'error':error,'checks':s['checks'],'elapsed_seconds':time.perf_counter()-s['start']}
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    unreal.log('DAS_ROGUE_CHARACTER_PIE '+json.dumps(result))
def phase(name,now):s['phase']=name;s['at']=now
def tick(delta):
    if s['done']:return
    try:
        now=time.perf_counter();age=now-s['at']
        assert now-s['start']<60,'Character test timed out'
        assert not p.get_editor_property('LastDasError'),p.get_editor_property('LastDasError')
        assert not pc.get_editor_property('LastDasError'),pc.get_editor_property('LastDasError')
        if s['phase']=='setup':
            movement.stop_movement_immediately()
            p.set_actor_location(unreal.Vector(350,-400,90),False,True)
            pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=cases[s['case']][1],roll=0))
            phase('settle',now);return
        if s['phase']=='settle':
            if age<0.3:return
            s['origin']=p.get_actor_location();phase('move',now);return
        if s['phase']=='move':
            if age<0.45:inject_key(cases[s['case']][0]);return
            start=s['origin'];end=p.get_actor_location();dx=end.x-start.x;dy=end.y-start.y
            key,yaw,ex,ey=cases[s['case']]
            along=dx*ex+dy*ey;cross=abs(dx*ey-dy*ex)
            assert along>30 and cross<15,(key,yaw,dx,dy)
            s['checks'].append({'key':key,'yaw':yaw,'delta':[dx,dy],'passed':True})
            movement.stop_movement_immediately();s['case']+=1
            if s['case']<len(cases):phase('setup',now)
            else:
                pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0))
                s['look_origin']=camera.get_world_location();s['looks']=p.get_editor_property('LookEvents')
                phase('look',now)
            return
        if s['phase']=='look':
            if age<0.9:inject_key('MouseX');return
            s['yaw_after_x']=pc.get_control_rotation().yaw
            assert s['yaw_after_x']>1,'Mouse X did not turn yaw'
            phase('look_y',now);return
        if s['phase']=='look_y':
            if age<0.9:inject_key('MouseY');return
            rotation=pc.get_control_rotation()
            assert abs(rotation.pitch)>1,'Mouse Y did not turn pitch'
            assert p.get_editor_property('LookEvents')>s['looks']
            assert (camera.get_world_location()-s['look_origin']).length()>1,'Camera did not orbit'
            s['checks'].append({'look':[rotation.pitch,rotation.yaw],'passed':True})
            s['jump_base']=p.get_actor_location().z;s['jump_peak']=s['jump_base']
            s['presses']=p.get_editor_property('JumpPresses');s['releases']=p.get_editor_property('JumpReleases')
            phase('jump',now);return
        if s['phase']=='jump':
            s['jump_peak']=max(s['jump_peak'],p.get_actor_location().z)
            if age<0.6:inject_key('SpaceBar')
            if age<2.2:return
            assert s['jump_peak']-s['jump_base']>40,'No actual jump displacement'
            assert p.get_editor_property('JumpPresses')==s['presses']+1,'Repeated Started'
            assert p.get_editor_property('JumpReleases')==s['releases']+1,'Jump release lost'
            assert abs(p.get_actor_location().z-s['jump_base'])<5,'Did not land'
            s['checks'].append({'jump_height':s['jump_peak']-s['jump_base'],'release':True,'landed':True})
            movement.stop_movement_immediately()
            p.set_actor_location(unreal.Vector(350,-400,90),False,True)
            chest=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_InteractiveChestHinged_C')
            pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(p.get_actor_location(),chest.get_actor_location()))
            s['chest']=chest;s['interacts']=pc.get_editor_property('SuccessfulInteractions')
            phase('interact',now);return
        if s['phase']=='interact':
            if age<0.3:return
            inject_action('IA_Interact');phase('chest',now);return
        if s['phase']=='chest':
            if age<0.7:return
            assert pc.get_editor_property('SuccessfulInteractions')==s['interacts']+1
            assert s['chest'].get_editor_property('CurrentAnimationPitch')>0
            s['checks'].append({'interaction':True,'chest_pitch':s['chest'].get_editor_property('CurrentAnimationPitch')})
            s['target']=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_TargetDummy_C')
            s['health']=s['target'].get_editor_property('Attributes').get_editor_property('Health')
            s['shots']=attack.get_editor_property('ProjectilesFired')
            phase('aim',now);return
        if s['phase']=='aim':
            # Aim from the actual third-person camera, accounting for its boom offset.
            pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_world_location(),s['target'].get_actor_location()))
            if age<0.8:return
            inject_action('IA_Fire');phase('impact',now);return
        if s['phase']=='impact':
            hp=s['target'].get_editor_property('Attributes').get_editor_property('Health')
            if hp==s['health']-25:
                assert attack.get_editor_property('ProjectilesFired')==s['shots']+1
                s['checks'].append({'fire':True,'target_health':hp})
                finish();return
            assert age<6,'Projectile failed to hit target: HP='+str(hp)
    except Exception:finish(traceback.format_exc())
s['handle']=unreal.register_slate_post_tick_callback(tick)
print('Character PIE checks scheduled')
