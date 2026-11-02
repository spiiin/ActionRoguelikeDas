"""Actual projectile collisions, Overwhelm damage windows and subscription lifetime."""
import gc
import json
import time
import traceback
from pathlib import Path
import unreal

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
target_class=unreal.load_class(None,'/Game/DasRogue/BP_RogueCombatTarget.BP_RogueCombatTarget_C')
projectile_class=unreal.load_class(None,'/Game/DasRogue/BP_MagicProjectileDemo.BP_MagicProjectileDemo_C')
stun_class=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionEffectStun.BP_RogueActionEffectStun_C')
overwhelm_class=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionEffectOverwhelm.BP_RogueActionEffectOverwhelm_C')
base_action=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueAction.BP_RogueAction_C')
dummy_class=unreal.load_class(None,'/Game/DasRogue/BP_TargetDummy.BP_TargetDummy_C')
assert all((target_class,projectile_class,stun_class,overwhelm_class,base_action,dummy_class))

def spawn(kind,location):return probe.call_method('Spawn',args=(kind,location,unreal.Rotator()))
def now():return unreal.GameplayStatics.get_time_seconds(world)
def tag(name):
    value=unreal.GameplayTag();assert value.import_text(name)
    return value
def actions(system,kind):return [a for a in system.get_editor_property('Actions') if a.get_class()==kind]
def stunned(system):return unreal.GameplayTagLibrary.has_tag(system.call_method('GetActiveTags'),tag('StatusEffect.Stunned'),True)
def shoot(target,damage=10.0,effect=None):
    position=target.get_actor_location()+unreal.Vector(-220,0,0)
    shot=spawn(projectile_class,position)
    assert shot
    shot.set_editor_property('AttackDamage',damage)
    shot.set_editor_property('EffectOnHit',effect)
    return shot
def health(target):return target.get_editor_property('Attributes').get_editor_property('Health')

target=spawn(target_class,unreal.Vector(1600,1600,200))
assert target
target.set_editor_property('DeathDelay',3.0)
system=target.get_editor_property('ActionSystem')
assert len(actions(system,overwhelm_class))==1
observer=actions(system,overwhelm_class)[0]
assert observer.get_editor_property('Listening')
s={'phase':'first','at':now(),'started':time.perf_counter(),'done':False,'checks':[],
   'observer':observer,'actors':[target],'shot':shoot(target)}
observer=None
result=Path(__file__).resolve().parents[1]/'Saved/Tests/rogue_overwhelm_pie.json'

def phase(name):s['phase']=name;s['at']=now()
def finish(error=None):
    s['done']=True;unreal.unregister_slate_post_tick_callback(s['handle'])
    for actor in s['actors']:
        if unreal.SystemLibrary.is_valid(actor):actor.destroy_actor()
    result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks']},indent=2))

def tick(delta):
    if s['done']:return
    try:
        assert time.perf_counter()-s['started']<60,'Overwhelm test timeout'
        for obj in (target,system):assert not obj.get_editor_property('LastDasError'),obj.get_editor_property('LastDasError')
        age=now()-s['at'];phase_name=s['phase']
        if age<.22:return
        if phase_name=='first':
            assert health(target)==90,health(target)
            assert s['observer'].get_editor_property('DamageEvents')==1
            assert s['observer'].get_editor_property('SummedRecentDamage')==10
            target.get_editor_property('Attributes').call_method('ApplyHealthChange',args=(pawn,5.0))
            assert s['observer'].get_editor_property('SummedRecentDamage')==10
            s['shot']=shoot(target);phase('threshold');return
        if phase_name=='threshold':
            assert health(target)==85 and stunned(system)
            assert s['observer'].get_editor_property('EffectsTriggered')==1
            assert s['observer'].get_editor_property('SummedRecentDamage')==0
            assert 'STUNNED' in str(target.get_editor_property('Label').get_editor_property('text'))
            s['checks'].append({'physical_hits_sum_damage':True,'healing_ignored':True,'threshold_stun_visible':True})
            s['shot']=shoot(target);phase('stunned_damage');return
        if phase_name=='stunned_damage':
            assert health(target)==75
            assert s['observer'].get_editor_property('DamageEvents')==2
            assert s['observer'].get_editor_property('EffectsTriggered')==1
            assert actions(system,stun_class)[0].get_editor_property('StackCount')==1
            phase('expiry');return
        if phase_name=='expiry':
            if age<2.65:return
            assert not stunned(system)
            assert 'STUNNED' not in str(target.get_editor_property('Label').get_editor_property('text'))
            s['checks'].append({'damage_during_stun_ignored':True,'no_stunlock':True})
            s['shot']=shoot(target,5.0);phase('window_first');return
        if phase_name=='window_first':
            assert health(target)==70
            assert s['observer'].get_editor_property('SummedRecentDamage')==5
            phase('window_wait');return
        if phase_name=='window_wait':
            if age<1.1:return
            s['shot']=shoot(target,5.0);phase('window_reset');return
        if phase_name=='window_reset':
            assert health(target)==65
            assert s['observer'].get_editor_property('SummedRecentDamage')==5
            assert not stunned(system)
            s['checks'].append({'expired_damage_window_resets':True})
            s['old_events']=s['observer'].get_editor_property('DamageEvents')
            assert system.call_method('RemoveAction',args=(s['observer'],))
            assert not s['observer'].get_editor_property('Listening')
            s['shot']=shoot(target);phase('unsubscribed');return
        if phase_name=='unsubscribed':
            assert health(target)==55
            assert s['observer'].get_editor_property('DamageEvents')==s['old_events']
            probe.call_method('Watch',args=(s['observer'],))
            s['observer']=None
            gc.collect();unreal.collect_garbage()
            assert not probe.call_method('WatchAlive'),'Removed listener retained by delegate'
            s['observer']=system.call_method('GrantAction',args=(overwhelm_class,))
            assert s['observer'] and s['observer'].get_editor_property('Listening')
            assert system.call_method('GrantAction',args=(overwhelm_class,))==s['observer']
            s['shot']=shoot(target);phase('resubscribed');return
        if phase_name=='resubscribed':
            assert health(target)==45
            assert s['observer'].get_editor_property('DamageEvents')==1,'Duplicate health listener'
            assert not stunned(system)
            s['checks'].append({'remove_unsubscribes':True,'listener_collected':True,'regrant_single_subscription':True})
            other=spawn(pawn.get_class(),unreal.Vector(1600,2300,200));s['actors'].append(other)
            other.get_editor_property('character_movement').disable_movement()
            s['other']=other;s['other_system']=other.get_editor_property('ActionSystem')
            s['shot']=shoot(other,0.0,stun_class);phase('zero_damage');return
        if phase_name=='zero_damage':
            assert health(s['other'])==100 and stunned(s['other_system'])
            s['shot']=shoot(s['other'],10.0,stun_class);phase('direct_effect');return
        if phase_name=='direct_effect':
            assert health(s['other'])==90
            assert len(actions(s['other_system'],stun_class))==1
            assert actions(s['other_system'],stun_class)[0].get_editor_property('StackCount')==2
            s['checks'].append({'zero_damage_hit_applies_effect':True,'on_hit_effect_stacks':True})
            s['other_system'].call_method('RemoveAction',args=(actions(s['other_system'],stun_class)[0],))
            s['shot']=shoot(s['other'],10.0,base_action);phase('invalid_class');return
        if phase_name=='invalid_class':
            assert health(s['other'])==80 and len(s['other_system'].get_editor_property('Actions'))==2
            dummy=spawn(dummy_class,unreal.Vector(1600,3000,200));s['actors'].append(dummy);s['dummy']=dummy
            s['shot']=shoot(dummy,10.0,stun_class);phase('no_system');return
        if phase_name=='no_system':
            assert health(s['dummy'])==90
            s['checks'].append({'non_effect_class_rejected':True,'target_without_action_system_supported':True})
            s['shot']=shoot(target,100.0,stun_class);phase('death');return
        if phase_name=='death':
            assert target.get_editor_property('Dead') and not system.get_editor_property('Enabled')
            assert len(system.get_editor_property('Actions'))==0
            assert not s['observer'].get_editor_property('Listening')
            assert not s['observer'].call_method('IsRunning')
            s['checks'].append({'lethal_hit_cleans_effects_and_subscription':True})
            finish()
    except Exception:finish(traceback.format_exc())

s['handle']=unreal.register_slate_post_tick_callback(tick)
