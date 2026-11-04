"""PIE: Enhanced Input, shared attack lifecycle, teleport races and collision failure."""
import json
import time
import traceback
from pathlib import Path
import unreal

w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
p=unreal.GameplayStatics.get_player_pawn(w,0)
pc=unreal.GameplayStatics.get_player_controller(w,0)
system=p.get_editor_property('ActionSystem')
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor)
           if a.get_class().get_name()=='BP_RogueTeleportProbe_C')
probe.set_tick_group(unreal.TickingGroup.TG_POST_UPDATE_WORK)
probe.set_actor_tick_enabled(True)
kind=unreal.load_class(None,'/Game/DasRogue/Projectiles/BP_RogueProjectileTeleport.BP_RogueProjectileTeleport_C')
inputs=max([v for v in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem)
            if v.get_outer().get_class().get_name()=='LocalPlayer'],
           key=lambda v:int(v.get_outer().get_name().rsplit('_',1)[-1]))

def prop(obj,name):return obj.get_editor_property(name)
def live(obj):return obj is not None and unreal.SystemLibrary.is_valid(obj)
def now():return unreal.GameplayStatics.get_time_seconds(w)
def tag(name):
    value=unreal.GameplayTag();assert value.import_text(name);return value
secondary=system.call_method('FindAction',args=(tag('Action.SecondaryAttack'),))
special=system.call_method('FindAction',args=(tag('Action.SpecialAttack'),))
assert secondary and special and secondary.get_outer()==system and special.get_outer()==system
rage=tag('Attribute.Rage')
assert dict(prop(secondary,'ActivationCost'))=={'Attribute.Rage':25.0}
assert system.call_method('GetAttributeValue',args=(rage,))==0
assert not secondary.call_method('CanStart')
system.call_method('ApplyAttributeChange',args=(rage,50.0))
s={'phase':'blackhole','at':now(),'start':time.perf_counter(),'done':False,'checks':[]}
receipt=Path('C:/src/ActionRoguelikeDas/Saved/Tests/rogue_additional_attacks_pie.json')

def phase(name):s['phase']=name;s['at']=now()
def track(projectile):
    probe.call_method('Watch',args=(projectile,))
    return projectile
def spawn(location,pawn=p):return track(probe.call_method('Spawn',args=(kind,location,pawn)))
def inject(name):inputs.inject_input_vector_for_action(unreal.load_asset('/Game/DasRogue/Input/'+name),unreal.Vector(1,0,0),[],[])
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    receipt.parent.mkdir(parents=True,exist_ok=True)
    diagnostic={'phase':s['phase'],'age':now()-s['at'],'result':s.get('teleport_result'),
                'pawn':str(p.get_actor_location()),'origin':str(s.get('origin'))}
    if live(s.get('projectile')):
        actor=s['projectile']
        diagnostic['projectile']={name:str(prop(actor,name)) for name in
            ['HasImpacted','ImpactCount','LastImpactActor','TeleportAttempts','TeleportSucceeded']}
        diagnostic['location']=str(actor.get_actor_location())
        diagnostic['velocity']=str(actor.get_velocity())
    receipt.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks'],'diagnostic':diagnostic},indent=2))

p.get_editor_property('character_movement').disable_movement()
p.set_actor_location(unreal.Vector(20000,-5000,1000),False,True)
pc.set_control_rotation(unreal.Rotator(pitch=0,yaw=0,roll=0))

def tick(delta):
    try:
        assert time.perf_counter()-s['start']<35,s['phase']
        s['teleport_result']={'attempts':prop(probe,'Attempts'),'success':prop(probe,'Success')}
        for obj in [p,pc,system,probe]:
            assert not prop(obj,'LastDasError'),prop(obj,'LastDasError')
        if live(s.get('projectile')):
            assert not prop(s['projectile'],'LastDasError'),prop(s['projectile'],'LastDasError')
        age=now()-s['at'];state=s['phase']
        if state=='blackhole':
            inject('IA_SecondaryAttack')
            if secondary.call_method('IsRunning'):
                assert not special.call_method('CanStart')
                assert not system.call_method('StartAction',args=(tag('Action.Sprint'),))
            if not prop(secondary,'ProjectilesFired'):return
            hole=prop(secondary,'LastProjectile')
            assert live(hole) and hole.get_class().get_name()=='BP_BlackholeAttackProjectile_C'
            assert not prop(hole,'LastDasError'),prop(hole,'LastDasError')
            assert 490<hole.get_velocity().length()<510
            assert prop(secondary,'CooldownTime')==.5 and not secondary.call_method('IsRunning')
            assert not system.call_method('StartAction',args=(tag('Action.SecondaryAttack'),))
            assert system.call_method('GetAttributeValue',args=(rage,))==25
            s['checks'].append('blackhole_requires_and_consumes_25_Rage_and_attack_tag_blocks_other_abilities')
            s['checks'].append('F_EnhancedInput_launches_blackhole_with_shared_windup_and_cooldown')
            hole.destroy_actor();s['origin']=p.get_actor_location();phase('special');return
        if state=='special':
            inject('IA_SpecialAttack')
            if not prop(special,'ProjectilesFired'):return
            s['projectile']=track(prop(special,'LastProjectile'));s['born']=now()
            assert live(s['projectile']) and prop(s['projectile'],'InitialSpeed')==6000
            assert (p.get_actor_location()-s['origin']).length()<1
            s['checks'].append('Q_EnhancedInput_launches_teleport_projectile')
            phase('flight');return
        if state=='flight':
            projectile=s['projectile']
            if not prop(projectile,'HasImpacted'):
                assert now()-s['born']<.3;return
            assert prop(projectile,'ImpactCount')==1 and not projectile.get_actor_enable_collision()
            assert projectile.get_velocity().length()<1 and prop(projectile,'hidden')
            s['destination']=projectile.get_actor_location()
            assert (p.get_actor_location()-s['origin']).length()<1
            projectile.call_method('StartDelayedTeleport')
            assert prop(projectile,'ImpactCount')==1
            s['checks'].append('detonation_stops_hides_and_disables_collision_once')
            phase('teleport');return
        if state=='teleport':
            if live(s['projectile']):
                if age<.14:assert (p.get_actor_location()-s['origin']).length()<1
                assert age<.4;return
            assert (p.get_actor_location()-s['destination']).length()<2
            assert age>=.15
            assert s['teleport_result']=={'attempts':1,'success':True}
            s['checks'].append('secondary_delay_then_native_teleport_preserves_destination')
            p.get_editor_property('character_movement').disable_movement()
            p.set_actor_location(unreal.Vector(20000,-1000,1000),False,True)
            s['origin']=p.get_actor_location()
            s['projectile']=spawn(unreal.Vector(20000,0,1000));phase('impact');return
        if state=='impact':
            projectile=s['projectile']
            if not prop(projectile,'HasImpacted'):assert age<.2;return
            details={'age':age,'count':prop(projectile,'ImpactCount'),
                     'actor':str(prop(projectile,'LastImpactActor')),'location':str(projectile.get_actor_location())}
            assert age<.2 and prop(projectile,'ImpactCount')==1,details
            assert prop(projectile,'LastImpactActor').get_actor_label()=='Teleport impact test wall'
            s['destination']=projectile.get_actor_location();phase('impact_wait');return
        if state=='impact_wait':
            if live(s['projectile']):assert age<.4;return
            assert age>=.15 and s['teleport_result']['attempts']==1
            if s['teleport_result']['success']:
                assert (p.get_actor_location()-s['destination']).length()<150
            else:
                assert (p.get_actor_location()-s['origin']).length()<1
            s['checks'].append('real_hit_cancels_flight_timer_and_honors_native_teleport_collision_result')
            p.get_editor_property('character_movement').disable_movement()
            p.set_actor_location(unreal.Vector(20000,-1000,1000),False,True)
            s['origin']=p.get_actor_location()
            s['projectile']=spawn(unreal.Vector(25000,0,1000))
            s['projectile'].call_method('StartDelayedTeleport');phase('blocked');return
        if state=='blocked':
            if live(s['projectile']):assert age<.4;return
            assert (p.get_actor_location()-s['origin']).length()<1
            assert s['teleport_result']=={'attempts':1,'success':False}
            s['checks'].append('blocked_destination_leaves_pawn_in_place_and_releases_projectile')
            owner=probe.call_method('SpawnPawn',args=(unreal.Vector(30000,-2000,1000),))
            s['projectile']=spawn(unreal.Vector(30000,0,1000),owner)
            owner.destroy_actor();phase('owner_gone');return
        if state=='owner_gone':
            if live(s['projectile']):assert age<.6;return
            assert s['teleport_result']=={'attempts':0,'success':False}
            s['checks'].append('destroyed_instigator_does_not_leave_unsafe_timer_callback')
            s['projectile']=spawn(unreal.Vector(30000,0,1000))
            s['projectile'].call_method('StartDelayedTeleport')
            s['projectile'].destroy_actor();s['origin']=p.get_actor_location();phase('destroyed');return
        if state=='destroyed':
            if age<.5:return
            assert (p.get_actor_location()-s['origin']).length()<1
            assert s['teleport_result']['attempts']==0
            s['checks'].append('destroyed_projectile_cancels_pending_teleport')
            s['fired']=prop(special,'ProjectilesFired')
            assert system.call_method('StartAction',args=(tag('Action.SpecialAttack'),))
            system.call_method('StopAction',args=(tag('Action.SpecialAttack'),))
            phase('cancel');return
        if state=='cancel':
            if age<.6:return
            assert prop(special,'ProjectilesFired')==s['fired']
            assert secondary.call_method('CanStart') and special.call_method('CanStart')
            sprinting=unreal.GameplayTagLibrary.make_gameplay_tag_container_from_array([tag('StatusEffect.Sprinting')])
            system.call_method('AppendActiveTags',args=(sprinting,))
            assert not secondary.call_method('CanStart') and not special.call_method('CanStart')
            system.call_method('RemoveActiveTags',args=(sprinting,))
            stunned=unreal.GameplayTagLibrary.make_gameplay_tag_container_from_array([tag('StatusEffect.Stunned')])
            system.call_method('AppendActiveTags',args=(stunned,))
            assert not secondary.call_method('CanStart') and not special.call_method('CanStart')
            system.call_method('RemoveActiveTags',args=(stunned,))
            s['checks'].append('canceling_windup_prevents_shot_and_stun_blocks_both_attacks')
            finish()
    except Exception:finish(traceback.format_exc())
s['handle']=unreal.register_slate_post_tick_callback(tick)
