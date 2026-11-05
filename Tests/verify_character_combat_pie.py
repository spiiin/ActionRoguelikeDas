"""Fresh PIE: native muzzle/cover collision, incoming projectile and terminal death."""
import unreal, time, json, traceback
from pathlib import Path
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert w
p=unreal.GameplayStatics.get_player_pawn(w,0)
pc=unreal.GameplayStatics.get_player_controller(w,0)
attack=next(a for a in p.get_editor_property('ActionSystem').get_editor_property('Actions') if a.get_class().get_name()=='BP_RogueActionProjectileAttack_C')
attributes=p.get_editor_property('Attributes')
assert attributes.get_editor_property('Health')==100
assert p.call_method('IsAlive')
camera=p.get_editor_property('CameraComponent')
movement=p.get_editor_property('character_movement')
target=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_TargetDummy_C')
# ChestTest is shared by editor demos. Give this scenario a deterministic clear lane.
movement.stop_movement_immediately()
p.set_actor_location(unreal.Vector(350,-400,90.15),False,True)
p.set_actor_rotation(unreal.Rotator(),False)
target.set_actor_scale3d(unreal.Vector(1,1,1))
target.set_actor_location(unreal.Vector(850,-400,113),False,True)
subsystems=[x for x in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if x.get_outer().get_class().get_name()=='LocalPlayer']
def hud_text(player,name):
    hud=player.get_editor_property('HUD')
    widget=hud.get_editor_property('HUD')
    assert widget and widget.is_in_viewport()
    tree=next(t for t in unreal.ObjectIterator(unreal.load_class(None,'/Script/UMG.WidgetTree')) if t.get_outer()==widget)
    return str(unreal.find_object(tree,name).get_text())

def index(x):
    try:return int(x.get_outer().get_name().rsplit('_',1)[-1])
    except ValueError:return -1
inputs=max(subsystems,key=index)
def inject(name,vector=unreal.Vector(1,0,0)):
    inputs.inject_input_vector_for_action(unreal.load_asset('/Game/DasRogue/Input/'+name),vector,[],[])
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_CombatProbe_C')
scope_probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
assert scope_probe.call_method('CheckCallScope',args=(False,)), 'Normal call scope leaked'
assert scope_probe.call_method('CheckCallScope',args=(True,)), 'Early-return call scope leaked'
assert scope_probe.call_method('CheckFailedCallScope'), 'Failed scope did not release its frame or preserve the error message'
def spawn(kind,location,rotation):
    actor=probe.call_method('Spawn',args=(kind,location,rotation))
    assert actor
    return actor
old_idle=unreal.SystemLibrary.get_console_variable_int_value('t.IdleWhenNotForeground')
unreal.SystemLibrary.execute_console_command(w,'t.IdleWhenNotForeground 0')
s={'phase':'aim','start':time.perf_counter(),'at':time.perf_counter(),'checks':[{'scoped_call_frames_release_normal_early_error':True}],'done':False,'shots':attack.get_editor_property('ProjectilesFired')}
receipt=Path('C:/src/ActionRoguelikeDas/Saved/Tests/rogue_character_combat_pie.json')
def phase(name,now):s['phase']=name;s['at']=now
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    if s.get('wall') and unreal.SystemLibrary.is_valid(s['wall']):s['wall'].destroy_actor()
    unreal.SystemLibrary.execute_console_command(w,'t.IdleWhenNotForeground '+str(old_idle))
    result={'passed':error is None,'error':error,'checks':s['checks'],'shot':s.get('shot'),'elapsed_seconds':time.perf_counter()-s['start']}
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps(result,indent=2),encoding='utf-8')
    unreal.log('DAS_ROGUE_CHARACTER_COMBAT_PIE '+json.dumps(result))
def tick(delta):
    if s['done']:return
    try:
        now=time.perf_counter();age=now-s['at']
        assert now-s['start']<60,'Combat check timed out'
        for actor in [p,pc,attributes]:assert not actor.get_editor_property('LastDasError'),actor.get_editor_property('LastDasError')
        if s['phase']=='aim':
            pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_world_location(),target.get_actor_location()))
            if age<0.9:return
            s['camera']=camera.get_world_location();s['pawn']=p.get_actor_location()
            inject('IA_Fire');phase('target_hit',now);return
        if s['phase']=='target_hit':
            mesh=p.get_editor_property('mesh')
            socket=attack.get_editor_property('MuzzleSocketName')
            if attack.get_editor_property('ProjectilesFired')>s['shots'] and 'socket_at_shot' not in s:
                if mesh.does_socket_exist(socket):s['socket_at_shot']=mesh.get_socket_location(socket)
            hp=target.get_editor_property('Attributes').get_editor_property('Health')
            s['shot']={name:str(value) for name,value in {
                'fired':attack.get_editor_property('ProjectilesFired'),
                'blocked':attack.get_editor_property('BlockedShots'),
                'pawn':p.get_actor_location(), 'rotation':p.get_actor_rotation(),
                'camera':camera.get_world_location(), 'target':target.get_actor_location(),
                'muzzle':attack.get_editor_property('LastMuzzleLocation'),
                'aim':attack.get_editor_property('LastAimPoint'),
                'controls':pc.get_control_rotation(),
                'pawn_health':attributes.get_editor_property('Health'),
            }.items()}
            projectile=attack.get_editor_property('LastProjectile')
            if projectile and unreal.SystemLibrary.is_valid(projectile):
                s['shot']['projectile']=str(projectile.get_actor_location())
                s['shot']['projectile_velocity']=str(projectile.get_velocity())
            if hp==100:
                assert age<5,'Shot did not reach camera target'
                return
            assert hp==49
            assert attack.get_editor_property('ProjectilesFired')==s['shots']+1
            muzzle=attack.get_editor_property('LastMuzzleLocation')
            if 'socket_at_shot' in s:
                error=(muzzle-s['socket_at_shot']).length()
                assert error<10,'Muzzle differs from the animated socket at the shot: '+str(error)
            else:
                assert (muzzle-s['pawn']).length()<100,'Fallback muzzle is not anchored to pawn'
            assert (muzzle-s['camera']).length()>200,'Shot still originates at camera'
            assert attributes.get_editor_property('Health')==100,'Self hit'
            s['checks'].append({'camera_target_hit':hp,'muzzle_to_pawn':(muzzle-s['pawn']).length(),'muzzle_to_camera':(muzzle-s['camera']).length(),'self_ignored':True})
            movement.stop_movement_immediately()
            p.set_actor_location(unreal.Vector(350,-400,73.15),False,True)
            # Point the animated muzzle through the wall for the cover test.
            p.set_actor_rotation(unreal.Rotator(),False)
            target.set_actor_location(unreal.Vector(550,-400,113),False,True)
            pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0))
            s['wall']=spawn(unreal.StaticMeshActor,unreal.Vector(390,-400,113),unreal.Rotator())
            mesh=s['wall'].get_editor_property('static_mesh_component')
            mesh.set_mobility(unreal.ComponentMobility.MOVABLE)
            mesh.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
            s['wall'].set_actor_scale3d(unreal.Vector(.08,2,2))
            mesh.set_collision_profile_name('BlockAll')
            phase('cover_aim',now);return
        if s['phase']=='cover_aim':
            if age<0.8:return
            inject('IA_Fire');phase('cover',now);return
        if s['phase']=='cover':
            if age<1.0:return
            assert attack.get_editor_property('ProjectilesFired')==s['shots']+2,'Clipped muzzle should fire into cover'
            muzzle=attack.get_editor_property('LastMuzzleLocation')
            assert 350<muzzle.x<374,'Muzzle spawned beyond cover: '+str(muzzle)
            assert target.get_editor_property('Attributes').get_editor_property('Health')==49,'Shot passed through cover'
            assert not [a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_MagicProjectileDemo_C'],'Covered projectile did not hit near wall'
            s['checks'].append({'near_cover_muzzle_x':muzzle.x,'cover_blocks_damage':True})
            s['wall'].destroy_actor();s['wall']=None
            kind=unreal.load_class(None,'/Game/DasRogue/BP_MagicProjectileDemo.BP_MagicProjectileDemo_C')
            s['incoming']=spawn(kind,unreal.Vector(480,-400,73.15),unreal.Rotator(pitch=0,yaw=180,roll=0))
            # This scenario measures direct damage/death; Burning is covered separately.
            s['incoming'].set_editor_property('EffectOnHit',None)
            phase('incoming',now);return
        if s['phase']=='incoming':
            hp=attributes.get_editor_property('Health')
            if hp==100:
                assert age<5,'Incoming projectile did not damage capsule'
                return
            assert hp==49
            assert '49 / 100' in hud_text(pc,'HealthText')
            assert '38 / 100' in hud_text(pc,'RageText')
            rage_tag=unreal.GameplayTag();assert rage_tag.import_text('Attribute.Rage')
            assert abs(p.get_editor_property('ActionSystem').call_method('GetAttributeValue',args=(rage_tag,))-38.25)<.001
            assert 'COINS  0'==hud_text(pc,'CoinsText')
            assert p.call_method('IsAlive')
            s['checks'].append({'incoming_projectile_health':hp})
            s['hurt']=0;phase('hurt_press',now);return
        if s['phase']=='hurt_press':
            inject('IA_TestDamage');s['hurt']+=1
            phase('hurt_release',now);return
        if s['phase']=='hurt_release':
            if age<0.8:return
            hp=attributes.get_editor_property('Health');expected=max(49-25*s['hurt'],0)
            assert hp==expected,(hp,expected)
            s['checks'].append({'H_press':s['hurt'],'health':hp})
            if hp>0:phase('hurt_press',now);return
            assert p.get_editor_property('Dead')
            assert p.get_editor_property('DeathCount')==1
            assert not p.call_method('IsAlive')
            assert movement.get_editor_property('movement_mode')==unreal.MovementMode.MOVE_NONE
            assert '0 / 100' in hud_text(pc,'HealthText')
            s['position']=p.get_actor_location();s['rotation']=pc.get_control_rotation()
            s['final_shots']=attack.get_editor_property('ProjectilesFired')
            s['interacts']=pc.get_editor_property('InteractPresses')
            s['events']=[p.get_editor_property(k) for k in ['MoveEvents','LookEvents','JumpPresses']]
            s['changes']=attributes.get_editor_property('HealthChanges')
            phase('dead_input',now);return
        if s['phase']=='dead_input':
            if age<1.2:
                inject('IA_Move');inject('IA_Look');inject('IA_Jump');inject('IA_Fire');inject('IA_Interact');inject('IA_TestDamage')
                return
            assert attack.get_editor_property('ProjectilesFired')==s['final_shots'],'Dead player fired'
            assert pc.get_editor_property('InteractPresses')==s['interacts'],'Dead player interacted'
            assert [p.get_editor_property(k) for k in ['MoveEvents','LookEvents','JumpPresses']]==s['events']
            assert (p.get_actor_location()-s['position']).length()<.01
            assert abs(pc.get_control_rotation().yaw-s['rotation'].yaw)<.01
            assert attributes.get_editor_property('HealthChanges')==s['changes']
            assert p.get_editor_property('DeathCount')==1
            s['checks'].append({'death_once':True,'dead_input_disabled':True})
            finish()
    except Exception:finish(traceback.format_exc())
s['handle']=unreal.register_slate_post_tick_callback(tick)
print('Character combat PIE checks scheduled')


def teardown():
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in list(actors.get_all_level_actors()):
        if actor.get_class().get_name()=='BP_CombatProbe_C':actors.destroy_actor(actor)
