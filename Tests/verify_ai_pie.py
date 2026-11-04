"""Real UE perception, controller movement and projectile damage; no mocked AI decisions."""
import json
import time
import traceback
from pathlib import Path
import unreal

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
player=unreal.GameplayStatics.get_player_controller(world,0)
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueAICharacter.BP_RogueAICharacter_C')
assert kind
for old in unreal.GameplayStatics.get_all_actors_of_class(world,kind):
    controller=old.get_controller()
    if controller:controller.destroy_actor()
    old.destroy_actor()
attributes=pawn.get_editor_property('Attributes')
assert attributes.get_owner()==pawn, 'Player Attributes does not refer to its own live component'
damage_probe={'native_calls':0,'last_damage':0.0}
def observe_native_damage(damaged_actor,damage,damage_type,instigated_by,damage_causer):
    damage_probe['native_calls']+=1
    damage_probe['last_damage']=damage
pawn.on_take_any_damage.add_callable(observe_native_damage)
probe.call_method('ConfigureHealth',args=(attributes,1000.0))
assert pawn.get_editor_property('Attributes')==attributes and attributes.get_owner()==pawn, 'Health setup replaced the component'
assert attributes.get_editor_property('HealthMax')==1000.0 and attributes.get_editor_property('Health')==1000.0
pawn.set_actor_location(unreal.Vector(2800,0,96),False,True)
pawn.get_editor_property('character_movement').disable_movement()
enemy=probe.call_method('Spawn',args=(kind,unreal.Vector(4000,0,96),unreal.Rotator(0,180,0)))
assert enemy
controller=enemy.get_controller()
assert controller and controller.get_class().get_name()=='BP_RogueAIController_C'
system=enemy.get_editor_property('ActionSystem')

def tag(name):
    value=unreal.GameplayTag();assert value.import_text(name);return value

attack=system.call_method('FindAction',args=(tag('Action.PrimaryAttack'),))
assert attack,'AI ranged action was not granted'
stun_kind=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionEffectStun.BP_RogueActionEffectStun_C')
assert stun_kind
result=Path('C:/src/ActionRoguelikeDas/Saved/Tests/rogue_ai_pie.json')
s={'phase':'sight','at':unreal.GameplayStatics.get_time_seconds(world),'started':time.perf_counter(),
   'origin':enemy.get_actor_location(),'actors':[enemy],'checks':[{'runtime_health_setup_preserves_component':True}],'done':False}

def now():return unreal.GameplayStatics.get_time_seconds(world)

def phase(name):s.update(phase=name,at=now())

def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    pawn.on_take_any_damage.remove_callable(observe_native_damage)
    for actor in s['actors']:
        if unreal.SystemLibrary.is_valid(actor):
            if isinstance(actor,unreal.Pawn):
                ai=actor.get_controller()
                if ai:ai.destroy_actor()
            actor.destroy_actor()
    result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks']},indent=2))

def tick(delta):
    if s['done']:return
    try:
        assert time.perf_counter()-s['started']<40,'AI test timed out in '+s['phase']
        for obj in (enemy,system):
            if unreal.SystemLibrary.is_valid(obj):assert not obj.get_editor_property('LastDasError'),obj.get_editor_property('LastDasError')
        if unreal.SystemLibrary.is_valid(controller):
            # Generic Blueprint parents retain their diagnostic in cooked class data; runtime errors are also log-gated.
            pass
        age=now()-s['at']
        if s['phase']=='sight':
            if age<.8:return
            assert controller.get_editor_property('SightEvents')>0,'Native sight did not report player'
            assert enemy.get_editor_property('Target')==pawn
            assert controller.get_editor_property('MoveRequests')>0
            assert (enemy.get_actor_location()-s['origin']).length()>30,'Enemy did not pursue target'
            s['checks'].append({'native_sight_and_direct_pursuit':True})
            phase('attack');return
        if s['phase']=='attack':
            if attributes.get_editor_property('Health')>=1000 and age<6:return
            assert controller.get_editor_property('AttackRequests')>0
            assert attack.get_editor_property('ProjectilesFired')>0
            if attributes.get_editor_property('Health')>=1000:
                def xyz(v):return [v.x,v.y,v.z]
                last=attack.get_editor_property('LastProjectile')
                details={'health':attributes.get_editor_property('Health'),'enemy_health':enemy.get_editor_property('Attributes').get_editor_property('Health'),'enemy_hits':enemy.get_editor_property('Hits'),'can_be_damaged':pawn.get_editor_property('can_be_damaged'),
                         'pawn':xyz(pawn.get_actor_location()),'enemy':xyz(enemy.get_actor_location()),
                         'aim':xyz(attack.get_editor_property('LastAimPoint')),
                         'muzzle':xyz(attack.get_editor_property('LastMuzzleLocation')),
                         'fired':attack.get_editor_property('ProjectilesFired'),
                         'blocked':attack.get_editor_property('BlockedShots'),
                         'last_projectile':str(last),'capsule_profile':str(pawn.get_editor_property('capsule_component').get_collision_profile_name())}
                if last:
                    try:
                        details.update(projectile_location=xyz(last.get_actor_location()),
                                       projectile_forward=xyz(last.get_actor_forward_vector()),
                                       projectile_impacted=last.get_editor_property('HasImpacted'),
                                       projectile_damage=last.get_editor_property('AttackDamage'),
                                       damage_attempts=last.get_editor_property('DamageAttempts'),
                                       damage_applied=last.get_editor_property('LastDamageApplied'),
                                       projectile_source=last.get_editor_property('LifecycleScript'),
                                       projectile_instigator=str(last.get_editor_property('instigator')),
                                       hit_actor=str(last.get_editor_property('LastImpactActor')),
                                       hit_point=xyz(last.get_editor_property('LastImpactPoint')),
                                       hit_forward=xyz(last.get_editor_property('LastImpactForward')),
                                       projectile_error=last.get_editor_property('LastDasError'))
                    except Exception as inspection:
                        details['pending_actor_inspection']=str(inspection)
                details['health_changes']=attributes.get_editor_property('HealthChanges')
                details['attribute_owner']=str(attributes.get_owner())
                details['attribute_source']=attributes.get_editor_property('LifecycleScript')
                details['native_damage_calls']=damage_probe['native_calls']
                details['matching_components']=[str(c) for c in pawn.get_components_by_class(attributes.get_class())]
                details['attribute_error']=attributes.get_editor_property('LastDasError')
                controller.set_editor_property('BrainEnabled',False)
                system.call_method('StopAction',args=(tag('Action.PrimaryAttack'),))
                details['direct_damage_return']=unreal.GameplayStatics.apply_damage(pawn,1.0,player,pawn,None)
                s['miss_details']=details
                phase('direct_damage_probe');return
            assert attributes.get_editor_property('LastInstigator')==enemy,'Wrong AI instigator'
            target=attack.get_editor_property('LastAimPoint')
            assert (target-pawn.get_actor_location()).length()<10,'AI aimed at camera rather than pawn'
            s['checks'].append({'action_attack_aim_and_real_ai_damage':True})
            effect=system.call_method('GrantAction',args=(stun_kind,));assert effect
            s['stun_effect']=effect;s['attacks']=controller.get_editor_property('AttackRequests')
            s['stun_origin']=enemy.get_actor_location();phase('stun');return
        if s['phase']=='direct_damage_probe':
            if age<.3:return
            details=s['miss_details']
            details['health_after_stable_causer']=attributes.get_editor_property('Health')
            details['health_changes_after_probe']=attributes.get_editor_property('HealthChanges')
            details['native_calls_after_probe']=damage_probe['native_calls']
            details['direct_attribute_result']=attributes.call_method('ApplyHealthChange',args=(pawn,-1.0))
            details['health_after_attribute_call']=attributes.get_editor_property('Health')
            s['checks'].append({'miss_diagnostics':details})
            raise AssertionError('AI projectile damage delivery: '+json.dumps(details))
        if s['phase']=='stun':
            if age<.55:return
            assert enemy.get_editor_property('Stunned')
            assert controller.get_editor_property('AttackRequests')==s['attacks'],'Attacked while stunned'
            assert (enemy.get_actor_location()-s['stun_origin']).length()<10
            movement=enemy.get_editor_property('character_movement')
            assert movement.get_editor_property('movement_mode')==unreal.MovementMode.MOVE_NONE
            base_speed=system.get_editor_property('BaseMoveSpeed')
            system.call_method('SetBaseMoveSpeed',args=(base_speed+25.0,))
            assert movement.get_editor_property('movement_mode')==unreal.MovementMode.MOVE_NONE
            system.call_method('SetBaseMoveSpeed',args=(base_speed,))
            s['checks'].append({'stun_stops_ai_attack_and_attribute_changes_do_not_restore_movement':True})
            phase('recover');return
        if s['phase']=='recover':
            if enemy.get_editor_property('Stunned') and age<4:return
            assert not enemy.get_editor_property('Stunned')
            controller.call_method('ForgetTarget')
            controller.stop_movement()
            controller.set_editor_property('AttackRange',0.0)
            enemy.set_actor_location(unreal.Vector(4000,0,96),False,True)
            enemy.set_actor_rotation(unreal.Rotator(0,0,0),True)
            s['heard']=controller.get_editor_property('HearingEvents')
            unreal.AISense_Hearing.report_noise_event(world,pawn.get_actor_location(),1.0,pawn,0.0,'AI_regression')
            phase('hearing');return
        if s['phase']=='hearing':
            if age<.5:return
            assert controller.get_editor_property('HearingEvents')>s['heard'],'Native hearing did not report noise'
            assert enemy.get_editor_property('Target')==pawn
            s['checks'].append({'native_hearing_acquires_instigator':True})
            controller.stop_movement()
            enemy.set_actor_location(unreal.Vector(4000,0,96),False,True)
            wall=probe.call_method('Spawn',args=(unreal.StaticMeshActor.static_class(),unreal.Vector(3400,0,200),unreal.Rotator()))
            wall.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
            wall.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
            wall.set_actor_scale3d(unreal.Vector(.4,12,5))
            wall.static_mesh_component.set_collision_profile_name('BlockAll')
            s['actors'].append(wall)
            controller.set_editor_property('AttackRange',2000.0)
            controller.set_editor_property('TargetMemory',.45)
            controller.set_editor_property('LastSensedAt',now())
            s['blocked_attacks']=controller.get_editor_property('AttackRequests')
            phase('occluded');return
        if s['phase']=='occluded':
            if age<1.0:return
            assert controller.get_editor_property('AttackRequests')==s['blocked_attacks'],'Attack started through wall'
            assert not enemy.get_editor_property('Target'),'Lost target was never forgotten'
            s['checks'].append({'occlusion_blocks_attack_and_memory_expires':True})
            unreal.GameplayStatics.apply_damage(enemy,500.0,player,pawn,None)
            phase('death');return
        if s['phase']=='death':
            if age<.4:return
            assert enemy.get_editor_property('Dead')
            assert not system.get_editor_property('Enabled')
            assert not controller.is_actor_tick_enabled(),'Dead AI thinker still running'
            for action in system.get_editor_property('Actions'):assert not action.call_method('IsRunning')
            s['checks'].append({'death_stops_actions_and_controller_thinker':True})
            finish()
    except Exception:finish(traceback.format_exc())

s['handle']=unreal.register_slate_post_tick_callback(tick)
