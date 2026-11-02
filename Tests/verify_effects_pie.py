"""Real PIE: automatic effect activation, timers, stacks and lifecycle cleanup."""
import gc
import json
import time
import traceback
from pathlib import Path
import unreal

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
system=pawn.get_editor_property('ActionSystem')
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
periodic=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RoguePeriodicEffect.BP_RoguePeriodicEffect_C')
fixed=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueFixedDurationEffect.BP_RogueFixedDurationEffect_C')
stun=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionEffectStun.BP_RogueActionEffectStun_C')
assert periodic and fixed and stun

def tag(name):
    value=unreal.GameplayTag()
    assert value.import_text(name)
    return value

def now():return unreal.GameplayStatics.get_time_seconds(world)
def grant(kind):
    effect=system.call_method('GrantAction',args=(kind,))
    if effect:assert effect.get_class()==kind,(kind,effect.get_class())
    return effect
def running(effect):return effect.call_method('IsRunning')
def count(effect):return effect.get_editor_property('PeriodicExecutions')
def rage():return system.call_method('GetAttributeValue',args=(tag('Attribute.Rage'),))
def has_stun():return unreal.GameplayTagLibrary.has_tag(system.call_method('GetActiveTags'),tag('StatusEffect.Stunned'),True)
def alive(obj):return unreal.SystemLibrary.is_valid(obj)
def collect():
    gc.collect()
    unreal.collect_garbage()

s={'phase':'stack','at':now(),'started':time.perf_counter(),'done':False,'checks':[]}
s['effect']=grant(periodic)
assert running(s['effect']) and s['effect'].get_outer()==system
collect()
assert running(s['effect'])
assert len(system.get_editor_property('Actions'))==3
s['checks'].append({'effect_auto_starts_and_survives_gc':True})
result=Path(__file__).resolve().parents[1]/'Saved/Tests/rogue_effects_pie.json'

def phase(name):s['phase']=name;s['at']=now()

def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks']},indent=2))

def tick(delta):
    if s['done']:return
    try:
        assert time.perf_counter()-s['started']<50,'Effect test timeout'
        assert not pawn.get_editor_property('LastDasError'),pawn.get_editor_property('LastDasError')
        assert not system.get_editor_property('LastDasError'),system.get_editor_property('LastDasError')
        age=now()-s['at']
        if s['phase']=='stack':
            if age<.25:return
            effect=s['effect']
            assert count(effect)>=2
            s['before_stack']=count(effect)
            assert grant(periodic)==effect
            assert effect.get_editor_property('StackCount')==2
            assert len(system.get_editor_property('Actions'))==3
            phase('refreshed');return
        if s['phase']=='refreshed':
            if age<.42:return
            assert running(s['effect']),'Stack failed to refresh duration'
            phase('expires');return
        if s['phase']=='expires':
            if running(s['effect']):return
            effect=s['effect'];ticks=count(effect)
            expected=s['before_stack']*3+(ticks-s['before_stack'])*6
            assert abs(rage()-expected)<.01,(rage(),expected,ticks)
            assert len(system.get_editor_property('Actions'))==2
            assert effect.get_editor_property('Stops')==1
            s['checks'].append({'one_instance_stacking':True,'duration_refreshed':True,'stack_scaled_ticks':ticks,'expiry_removes_effect':True})
            s['effect']=grant(fixed)
            phase('fixed_stack');return
        if s['phase']=='fixed_stack':
            if age<.4:return
            assert grant(fixed)==s['effect']
            phase('fixed_expiry');return
        if s['phase']=='fixed_expiry':
            if age<.25:return
            assert not running(s['effect']),'Fixed-duration stack incorrectly refreshed duration'
            assert count(s['effect'])==6,('Missing or duplicate boundary tick',count(s['effect']))
            s['checks'].append({'no_refresh_option':True,'final_boundary_tick_once':True})
            s['effect']=grant(periodic)
            phase('manual_remove');return
        if s['phase']=='manual_remove':
            if age<.22:return
            effect=s['effect']
            assert system.call_method('RemoveAction',args=(effect,))
            assert not running(effect) and effect.get_editor_property('Stops')==1
            assert not system.call_method('RemoveAction',args=(effect,))
            s['removed_ticks']=count(effect)
            phase('removed_idle');return
        if s['phase']=='removed_idle':
            if age<.3:return
            assert count(s['effect'])==s['removed_ticks'],'Removed periodic timer still executes'
            probe.call_method('Watch',args=(s['effect'],))
            s['effect']=None
            collect()
            assert not probe.call_method('WatchAlive'),'Removed effect retained by its timers'
            s['checks'].append({'manual_remove_no_recursion':True,'cancelled_timer_quiet':True,'removed_effect_collected':True})
            assert system.call_method('StartAction',args=(tag('Action.Sprint'),))
            s['effect']=grant(stun)
            assert has_stun()
            assert not system.call_method('FindAction',args=(tag('Action.Sprint'),)).call_method('IsRunning')
            assert not system.call_method('StartAction',args=(tag('Action.PrimaryAttack'),))
            assert not system.call_method('StartAction',args=(tag('Action.Sprint'),))
            phase('stun');return
        if s['phase']=='stun':
            if age<2.65:return
            assert not running(s['effect']) and not has_stun()
            assert system.call_method('StartAction',args=(tag('Action.Sprint'),))
            system.call_method('StopAction',args=(tag('Action.Sprint'),))
            s['checks'].append({'stun_cancels_and_blocks_actions':True,'natural_expiry_restores_actions':True})
            s['periodic']=grant(periodic);s['stun']=grant(stun)
            pawn.get_editor_property('Attributes').call_method('ApplyHealthChange',args=(pawn,-1000.0))
            assert pawn.get_editor_property('Dead') and not system.get_editor_property('Enabled')
            assert not running(s['periodic']) and not running(s['stun'])
            assert not has_stun() and len(system.get_editor_property('Actions'))==2
            assert grant(periodic) is None
            s['shutdown_ticks']=count(s['periodic'])
            second=probe.call_method('Spawn',args=(pawn.get_class(),unreal.Vector(-500,-500,100),unreal.Rotator()))
            other=second.get_editor_property('ActionSystem')
            s['orphan_effect']=other.call_method('GrantAction',args=(periodic,))
            second.destroy_actor()
            assert not running(s['orphan_effect'])
            phase('shutdown');return
        if s['phase']=='shutdown':
            if age<.7:return
            assert count(s['periodic'])==s['shutdown_ticks']
            assert count(s['orphan_effect'])==0
            s['checks'].append({'death_cleans_mutating_effect_array':True,'disabled_owner_rejects_grants':True,'endplay_cancels_effect_timers':True})
            finish()
    except Exception:finish(traceback.format_exc())

s['handle']=unreal.register_slate_post_tick_callback(tick)
