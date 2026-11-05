"""Original course combat parity: native collision, damage perception, flash, spread and ragdoll."""
import json,time,traceback
from pathlib import Path
import unreal

root=Path(__file__).resolve().parents[1]
reference=json.loads((root/'Saved/Tests/original_movement_reference.json').read_text())['combat']
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn=unreal.GameplayStatics.get_player_pawn(w,0)
player=unreal.GameplayStatics.get_player_controller(w,0)
base=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueAICharacter.BP_RogueAICharacter_C')
for old in unreal.GameplayStatics.get_all_actors_of_class(w,kind):
    c=old.get_controller()
    if c:c.destroy_actor()
    old.destroy_actor()
probe_kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueAIPresentationProbe.BP_RogueAIPresentationProbe_C')
probe=base.call_method('Spawn',args=(probe_kind,unreal.Vector(0,0,300),unreal.Rotator()))
assert probe
probe.call_method('ConfigureHealth',args=(pawn.get_editor_property('Attributes'),1000.0))
pawn.set_actor_location(unreal.Vector(3000,-1000,96),False,True)
pawn.get_editor_property('character_movement').stop_movement_immediately()
player.set_control_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0))
enemy=probe.call_method('Spawn',args=(kind,unreal.Vector(4200,-1000,96),unreal.Rotator(pitch=0,yaw=0,roll=0)))
controller=enemy.get_controller(); assert controller
controller.set_editor_property('NextThink',1e9)
mesh=enemy.get_editor_property('mesh'); assert enemy.get_editor_property('UsingExternalPresentation')
assert mesh.get_skeletal_mesh_asset().get_editor_property('physics_asset'),'Minion must have its real physics asset'
system=enemy.get_editor_property('ActionSystem')
def tag(name):
    t=unreal.GameplayTag();assert t.import_text(name);return t
attack=system.call_method('FindAction',args=(tag('Action.PrimaryAttack'),))
assert attack
expected_speed=reference['enemy']['attributes']['MoveSpeed']['Base']
assert expected_speed==450
assert abs(enemy.get_editor_property('character_movement').max_walk_speed-expected_speed)<.01
projectile_kind=unreal.load_class(None,'/Game/DasRogue/BP_RogueMagicProjectile.BP_RogueMagicProjectile_C')
expected_damage=reference['projectile']['values']['AttackDamage']
assert unreal.get_default_object(projectile_kind).get_editor_property('AttackDamage')==expected_damage
assert abs(pawn.get_editor_property('character_movement').max_walk_speed-550)<.01
samples=[attack.call_method('GetProjectileRotation',args=(unreal.Vector(),unreal.Vector(1000,0,0))) for i in range(96)]
spread=attack.get_editor_property('MaxBulletSpread')
assert spread==reference['ranged_tasks'][0]['MaxBulletSpread']==5 and all(0<=s.pitch<=spread and -spread<=s.yaw<=spread for s in samples)
assert max(s.pitch for s in samples)>3 and min(s.yaw for s in samples)<-3 and max(s.yaw for s in samples)>3
attack.set_editor_property('MaxBulletSpread',0.0)
zero=attack.call_method('GetProjectileRotation',args=(unreal.Vector(),unreal.Vector(1000,0,0)))
assert abs(zero.pitch)<.001 and abs(zero.yaw)<.001
attack.set_editor_property('MaxBulletSpread',spread)
flash=enemy.get_editor_property('HitFlash'); player_flash=pawn.get_editor_property('HitFlash')
assert flash.get_editor_property('OverlayMaterial') and player_flash.get_editor_property('OverlayMaterial')
assert not flash.get_editor_property('Visible') and mesh.get_editor_property('overlay_material_max_draw_distance')==1
s={'phase':'blind','at':0,'started':time.perf_counter(),'checks':['blueprint_balance_51_550_450','ranged_pitch_0_5_yaw_minus5_5_and_zero_spread','shared_overlay_material_initially_hidden'],'actors':[probe,enemy],'done':False}
def now():return unreal.GameplayStatics.get_time_seconds(w)
def phase(name):s['phase']=name;s['at']=now()
def finish(error=None):
    s['done']=True;unreal.unregister_slate_post_tick_callback(s['handle'])
    for actor in s['actors']:
        if unreal.SystemLibrary.is_valid(actor):
            if isinstance(actor,unreal.Pawn):
                c=actor.get_controller()
                if c:c.destroy_actor()
            actor.destroy_actor()
    (root/'Saved/Tests/rogue_combat_parity_pie.json').write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks'],'reference':reference,'overlay':s.get('overlay'),'isolated_effects':s.get('isolated_effects',[])},indent=2))
def tick(delta):
    if s['done'] or s.get('busy'):return
    s['busy']=True
    try:
        assert time.perf_counter()-s['started']<55,'Combat parity timeout in '+s['phase']
        for obj in (pawn,enemy,flash,player_flash):
            if unreal.SystemLibrary.is_valid(obj):assert not obj.get_editor_property('LastDasError'),obj.get_editor_property('LastDasError')
        age=now()-s['at'];state=s['phase']
        if state=='blind':
            if age<.5:return
            assert controller.get_editor_property('SightEvents')==0,'Fixture accidentally visible'
            unreal.GameplayStatics.apply_damage(enemy,5.0,player,pawn,None)
            phase('damage');return
        if state=='damage':
            if age<.25:return
            assert pawn in controller.get_editor_property('Perception').get_currently_perceived_actors(unreal.AISense_Damage),'Native damage sense not delivered'
            assert controller.get_editor_property('SightEvents')==0 and controller.get_editor_property('HearingEvents')==0
            assert enemy.get_editor_property('Target')==pawn
            assert flash.get_editor_property('Visible') and flash.get_editor_property('Flashes')==1
            assert abs(flash.get_editor_property('LastHitTime')-(now()-age))<.1
            assert mesh.get_editor_property('overlay_material_max_draw_distance')==0
            s['checks'].append('damage_behind_enemy_acquires_attacker_without_sight_or_noise')
            s['checks'].append('native_hit_timestamp_and_overlay_enable')
            # Damage must not cancel a pending shot or replace its animation.
            probe.call_method('FreezeBrain',args=(enemy,pawn))
            assert system.call_method('StartAction',args=(tag('Action.PrimaryAttack'),))
            s['shots']=attack.get_editor_property('ProjectilesFired')
            unreal.GameplayStatics.apply_damage(enemy,5.0,player,pawn,None)
            assert attack.call_method('IsRunning')
            phase('pending');return
        if state=='pending':
            if age<.6:return
            assert attack.get_editor_property('ProjectilesFired')==s['shots']+1
            assert enemy.get_editor_property('HitReactions')==0
            s['checks'].append('damage_preserves_pending_shot')
            friend=probe.call_method('Spawn',args=(kind,unreal.Vector(5200,-1000,96),unreal.Rotator()))
            s['actors'].append(friend)
            friend_controller=friend.get_controller();assert friend_controller
            probe.call_method('FreezeBrain',args=(friend,pawn))
            s['friend']=friend
            s['damage_sources']=controller.get_editor_property('Perception').get_currently_perceived_actors(unreal.AISense_Damage)
            # Re-enable only perception delivery; do not let the thinker move this fixture.
            controller.set_editor_property('BrainEnabled',True)
            controller.set_editor_property('NextThink',1e9)
            unreal.GameplayStatics.apply_damage(enemy,1.0,friend_controller,friend,None)
            phase('friendly');return
        if state=='friendly':
            if age<.3:return
            perceived=controller.get_editor_property('Perception').get_currently_perceived_actors(unreal.AISense_Damage)
            assert s['friend'] not in perceived,'Friendly controller published a damage stimulus'
            assert set(perceived)==set(s['damage_sources'])
            s['checks'].append('friendly_damage_does_not_publish_damage_stimulus')
            probe.call_method('FreezeBrain',args=(enemy,pawn))
            # The pending-shot check above fires a real projectile, which can
            # apply Burning. Its periodic damage must not restart the unrelated
            # overlay timer while this fixture measures two controlled hits.
            for shot in unreal.GameplayStatics.get_all_actors_of_class(w,projectile_kind):
                shot.destroy_actor()
            s['isolated_effects']=[]
            for effect in list(pawn.get_editor_property('ActionSystem').get_editor_property('Actions')):
                if effect.call_method('IsEffect') and effect.call_method('IsRunning'):
                    s['isolated_effects'].append(effect.get_class().get_name())
                    effect.call_method('StopAction')
            unreal.GameplayStatics.apply_damage(pawn,1.0,controller,enemy,None)
            assert player_flash.get_editor_property('Visible')
            phase('repeat');return
        if state=='repeat':
            if age<.6:return
            unreal.GameplayStatics.apply_damage(pawn,1.0,controller,enemy,None)
            s['last_hit']=now()
            s['expected_flashes']=player_flash.get_editor_property('Flashes')
            phase('old_timeout');return
        if state=='old_timeout':
            if age<.6:return
            assert player_flash.get_editor_property('Visible'),'Old flash timer hid a newer hit'
            s['checks'].append('repeated_damage_restarts_overlay_timer')
            phase('hidden');return
        if state=='hidden':
            if now()-s['last_hit']<1.1:return
            s['overlay']={'now':now(),'requested_hit':s['last_hit'],
                'actual_hit':player_flash.get_editor_property('LastHitTime'),
                'flashes':player_flash.get_editor_property('Flashes'),'expected':s['expected_flashes'],
                'visible':player_flash.get_editor_property('Visible'),
                'same_component':pawn.get_editor_property('HitFlash')==player_flash,
                'controller':controller.get_class().get_name()}
            assert s['overlay']['flashes']==s['overlay']['expected'], 'Unexpected damage in overlay fixture: '+str(s['overlay'])
            assert not player_flash.get_editor_property('Visible'), (
                f"overlay still visible: now={now()}, requested_hit={s['last_hit']}, "
                f"actual_hit={player_flash.get_editor_property('LastHitTime')}, "
                f"flashes={player_flash.get_editor_property('Flashes')}, expected={s['expected_flashes']}, "
                f"controller={controller.get_class().get_name()}")
            assert pawn.get_editor_property('mesh').get_editor_property('overlay_material_max_draw_distance')==1
            s['checks'].append('overlay_hides_one_second_after_last_hit')
            # Fire a real player attack, freeze its projectile and sweep its owner through it.
            pawn.set_actor_location(unreal.Vector(3000,-1500,96),False,True)
            player.set_control_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0))
            s['player_attack']=pawn.get_editor_property('ActionSystem').call_method('FindAction',args=(tag('Action.PrimaryAttack'),))
            assert pawn.get_editor_property('ActionSystem').call_method('StartAction',args=(tag('Action.PrimaryAttack'),))
            phase('own_projectile');return
        if state=='own_projectile':
            if age<.25:return
            projectile=s['player_attack'].get_editor_property('LastProjectile')
            assert unreal.SystemLibrary.is_valid(projectile)
            s['actors'].append(projectile)
            projectile.get_editor_property('ProjectileMovementComponent').stop_movement_immediately()
            start=pawn.get_actor_location()
            projectile.set_actor_location(start+unreal.Vector(100,0,0),False,True)
            pawn.set_actor_location(start+unreal.Vector(200,0,0),True,False)
            assert abs(pawn.get_actor_location().x-start.x-200)<1,'Owner sweep blocked on its own projectile'
            assert not projectile.get_editor_property('HasImpacted')
            projectile.destroy_actor()
            start=pawn.get_actor_location()
            foreign=probe.call_method('Spawn',args=(projectile_kind,start+unreal.Vector(100,0,0),unreal.Rotator()))
            assert foreign
            s['actors'].append(foreign)
            foreign.get_editor_property('ProjectileMovementComponent').stop_movement_immediately()
            pawn.set_actor_location(start+unreal.Vector(200,0,0),True,False)
            assert pawn.get_actor_location().x-start.x<150,'Control sweep did not block on a foreign projectile'
            if unreal.SystemLibrary.is_valid(foreign):foreign.destroy_actor()
            s['checks'].append('real_player_projectile_ignored_by_owner_sweep_foreign_projectile_blocks')
            unreal.GameplayStatics.apply_damage(enemy,1000.0,player,pawn,None)
            s['death_at']=now()
            phase('ragdoll');return
        if state=='ragdoll':
            if age<.3:return
            assert enemy.get_editor_property('Dead') and mesh.get_editor_property('pause_anims')
            assert str(mesh.get_collision_profile_name())=='Ragdoll'
            assert any(mesh.is_simulating_physics(mesh.get_bone_name(i)) for i in range(mesh.get_num_bones())),'No Minion physics bodies simulating'
            assert not system.get_editor_property('Enabled')
            assert not controller.is_actor_tick_enabled()
            assert enemy.get_editor_property('DeathAnimations')==0
            assert enemy.get_editor_property('capsule_component').get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION
            assert 9<enemy.get_life_span()<=10
            s['checks'].append('death_uses_real_ragdoll_paused_animation_and_disabled_capsule')
            phase('corpse');return
        if state=='corpse':
            if now()-s['death_at']<2.5:return
            assert unreal.SystemLibrary.is_valid(enemy),'Corpse vanished at the old two-second timeout'
            s['checks'].append('corpse_survives_old_two_second_timeout')
            phase('expire');return
        if state=='expire':
            elapsed=now()-s['death_at']
            if unreal.SystemLibrary.is_valid(enemy):assert elapsed<10.5;return
            assert elapsed>=9.9
            s['checks'].append('corpse_expires_after_ten_seconds')
            finish()
    except Exception:finish(traceback.format_exc())
    finally:s['busy']=False
phase('blind')
s['handle']=unreal.register_slate_post_tick_callback(tick)
