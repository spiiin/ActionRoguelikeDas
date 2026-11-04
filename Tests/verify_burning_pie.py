"""Source Burning: native damage, exact boundary tick, stacking and lifecycle."""
from pathlib import Path
import json,time,traceback
import unreal

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
effect_kind=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionEffectBurning.BP_RogueActionEffectBurning_C')
target_kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueBurningTarget.BP_RogueBurningTarget_C')
shot_kind=unreal.load_class(None,'/Game/DasRogue/BP_MagicProjectileDemo.BP_MagicProjectileDemo_C')
result=Path(unreal.Paths.project_saved_dir())/'Tests/rogue_burning_pie.json'
default=unreal.get_default_object(effect_kind)
assert default.get_editor_property('Duration')==3 and default.get_editor_property('Period')==1
assert default.get_editor_property('DamageToApply')==5 and default.get_editor_property('ResetDurationOnStackIncrease')
assert str(default.get_editor_property('ActionName').get_editor_property('tag_name'))=='None'
assert len(default.get_editor_property('GrantTags').get_editor_property('gameplay_tags'))==0
assert len(default.get_editor_property('BlockedTags').get_editor_property('gameplay_tags'))==0
assert unreal.get_default_object(shot_kind).get_editor_property('EffectOnHit')==effect_kind
bare=unreal.load_class(None,'/Game/DasRogue/BP_RogueMagicProjectile.BP_RogueMagicProjectile_C')
assert unreal.get_default_object(bare).get_editor_property('EffectOnHit') is None

def prop(obj,name):return obj.get_editor_property(name)
def now():return unreal.GameplayStatics.get_time_seconds(world)
def tag(name):
    value=unreal.GameplayTag();assert value.import_text(name);return value
def health(t):return prop(t['attributes'],'Health')
def damage_ticks(t):return prop(t['effect'],'DamageTicks')
def running(t):return prop(t['effect'],'bIsRunning')
def actions(t):return list(prop(t['system'],'Actions'))
def alive(obj):
    try:return unreal.SystemLibrary.is_valid(obj)
    except TypeError as error:
        if 'NativizeObject' in str(error):return False
        raise

s={'phase':'early','at':now(),'started':time.perf_counter(),'checks':['source_defaults_and_gameplay_projectile_configuration'],'done':False,'actors':[],'targets':{}}

def spawn(kind,where):
    actor=probe.call_method('Spawn',args=(kind,where,unreal.Rotator()))
    assert actor
    s['actors'].append(actor)
    return actor

def target(index,maximum=100):
    actor=spawn(target_kind,unreal.Vector(12000+index*500,-5000,1000))
    attributes=prop(actor,'Attributes')
    if maximum!=100:probe.call_method('ConfigureHealth',args=(attributes,float(maximum)))
    return {'actor':actor,'attributes':attributes,'system':prop(actor,'ActionSystem')}

def grant(t):return t['system'].call_method('GrantAction',args=(effect_kind,))

for index,name in enumerate(['single','stack','fixed','manual','lethal','deleted','flagged','zero']):
    t=target(index,2 if name=='lethal' else 100)
    if name=='flagged':t['actor'].set_editor_property('can_be_damaged',False)
    t['effect']=grant(t);assert t['effect'] and running(t)
    assert prop(t['effect'],'StackCount')==1 and len(actions(t))==1
    if name=='fixed':t['effect'].set_editor_property('ResetDurationOnStackIncrease',False)
    if name=='zero':t['effect'].set_editor_property('DamageToApply',0.0)
    s['targets'][name]=t

# Compare the flagged generic Actor with direct engine ApplyDamage, rather than
# assuming that bCanBeDamaged is implemented as immunity by AActor::TakeDamage.
native_reference=target(12)
native_reference['actor'].set_editor_property('can_be_damaged',False)
assert not prop(native_reference['actor'],'can_be_damaged')
assert not prop(s['targets']['flagged']['actor'],'can_be_damaged')
for _ in range(3):unreal.GameplayStatics.apply_damage(native_reference['actor'],5.0,None,None,None)
s['native_reference']=native_reference

# Keep the previous fractional-period boundary case as a regression for the
# shared effect implementation, independent of the player's granted abilities.
fractional=target(11)
fractional_kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueFixedDurationEffect.BP_RogueFixedDurationEffect_C')
assert fractional_kind
fractional['effect']=fractional['system'].call_method('GrantAction',args=(fractional_kind,))
s['fractional']=fractional

def phase(name):s.update(phase=name,at=now())

def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    result.parent.mkdir(parents=True,exist_ok=True)
    diagnostics={}
    for key,t in s['targets'].items():
        if alive(t['actor']):
            diagnostics[key]={'health':health(t),'damage_events':prop(t['actor'],'DamageEvents')}
            if t.get('effect'):
                diagnostics[key].update(damage_ticks=damage_ticks(t),periodic_executions=prop(t['effect'],'PeriodicExecutions'),running=running(t),stops=prop(t['effect'],'Stops'))
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks'],'diagnostics':diagnostics},indent=2))

def tick(delta):
    if s['done'] or s.get('busy'):return
    s['busy']=True
    try:
        assert time.perf_counter()-s['started']<45,s['phase']
        for t in s['targets'].values():
            if alive(t['actor']):
                for obj in [t['actor'],t['attributes'],t['system']]:assert not prop(obj,'LastDasError'),prop(obj,'LastDasError')
        age=now()-s['at'];name=s['phase'];targets=s['targets']
        if name=='early':
            if age<.25:return
            assert health(targets['single'])==100 and damage_ticks(targets['single'])==0
            manual=targets['manual']
            assert manual['system'].call_method('RemoveAction',args=(manual['effect'],))
            assert not running(manual) and prop(manual['effect'],'Stops')==1
            s['checks'].append('no_immediate_damage_and_explicit_removal_before_first_tick')
            phase('first');return
        if name=='first':
            if age<1.0:return
            fractional=s['fractional']
            assert not prop(fractional['effect'],'bIsRunning') and prop(fractional['effect'],'PeriodicExecutions')==6
            assert prop(fractional['effect'],'Stops')==1
            assert fractional['system'].call_method('GetAttributeValue',args=(tag('Attribute.Rage'),))==18
            s['checks'].append('fractional_period_regression_keeps_six_boundary_ticks')
            single=targets['single']
            assert health(single)==95 and damage_ticks(single)==1
            assert prop(single['actor'],'LastSource') is None and prop(single['actor'],'LastController') is None
            assert abs(single['system'].call_method('GetAttributeValue',args=(tag('Attribute.Rage'),))-3.75)<.001
            for key in ['stack','fixed']:
                t=targets[key]
                assert health(t)==95 and grant(t)==t['effect'] and len(actions(t))==1
                assert prop(t['effect'],'StackCount')==2
            lethal=targets['lethal']
            assert prop(lethal['actor'],'Dead') and health(lethal)==0
            assert not prop(lethal['system'],'Enabled') and not running(lethal) and not actions(lethal)
            assert damage_ticks(lethal)==1 and prop(lethal['actor'],'DamageEvents')==1
            deleted=targets['deleted'];assert damage_ticks(deleted)==1
            deleted['actor'].destroy_actor()
            s['checks'].append('native_any_damage_and_Rage_with_original_null_attribution')
            phase('cadence');return
        if name=='cadence':
            if age<.85:return
            t=targets['stack']
            assert damage_ticks(t)==2 and health(t)==85,'Stacking restarted the periodic cadence'
            s['checks'].append('one_instance_stacking_scales_damage_without_restarting_period')
            phase('original_expiry');return
        if name=='original_expiry':
            if age<1.2:return
            single=targets['single'];fixed=targets['fixed'];stack=targets['stack']
            assert not running(single) and damage_ticks(single)==3 and health(single)==85
            assert prop(single['effect'],'PeriodicExecutions')==3 and prop(single['effect'],'Stops')==1 and not actions(single)
            assert not running(fixed) and damage_ticks(fixed)==3 and health(fixed)==75 and not actions(fixed)
            assert running(stack) and damage_ticks(stack)==3 and health(stack)==75
            assert health(targets['manual'])==100 and damage_ticks(targets['manual'])==0
            assert damage_ticks(targets['deleted'])==1 and not alive(targets['deleted']['actor'])
            assert damage_ticks(targets['lethal'])==1
            flagged=targets['flagged'];reference=s['native_reference'];zero=targets['zero']
            assert not running(flagged) and damage_ticks(flagged)==3
            assert health(flagged)==health(reference)==85
            assert prop(flagged['actor'],'DamageEvents')==prop(reference['actor'],'DamageEvents')==3
            assert prop(flagged['effect'],'TotalDamageApplied')==15
            assert not running(zero) and damage_ticks(zero)==0 and health(zero)==100
            assert prop(zero['effect'],'PeriodicExecutions')==3 and prop(zero['actor'],'DamageEvents')==0
            s['checks']+=['three_due_ticks_including_duration_boundary_exactly_once','no_refresh_option_expires_on_original_deadline',
                'flagged_generic_actor_matches_direct_engine_ApplyDamage','zero_damage_does_not_emit_native_damage_events','manual_removal_death_and_owner_destruction_cancel_timers']
            s['reburn']=grant(single)
            assert s['reburn']!=single['effect'] and prop(s['reburn'],'StackCount')==1
            assert prop(s['reburn'],'DamageTicks')==0 and health(single)==85
            phase('refresh_expiry');return
        if name=='refresh_expiry':
            if age<1.2:return
            stack=targets['stack'];single=targets['single']
            assert not running(stack) and damage_ticks(stack)==4 and health(stack)==65 and not actions(stack)
            assert prop(s['reburn'],'DamageTicks')==1 and health(single)==80
            assert single['system'].call_method('RemoveAction',args=(s['reburn'],))
            s['checks']+=['refreshed_duration_expires_with_all_stacks_removed','reapplying_expired_effect_creates_fresh_state']
            for index,key,maximum in [(8,'hit',100),(9,'lethal_hit',40)]:
                t=target(index,maximum);targets[key]=t
                shot=spawn(shot_kind,t['actor'].get_actor_location()+unreal.Vector(-220,0,0))
                shot.set_editor_property('instigator',pawn)
                t['shot']=shot
            phase('impact');return
        if name=='impact':
            if age<.3:return
            t=targets['hit'];lethal=targets['lethal_hit']
            assert health(t)==49 and prop(t['actor'],'DamageEvents')==1
            assert not alive(t['shot']) and len(actions(t))==1
            t['effect']=actions(t)[0]
            assert t['effect'].get_class()==effect_kind and damage_ticks(t)==0
            assert prop(lethal['actor'],'Dead') and health(lethal)==0 and not actions(lethal)
            s['checks'].append('real_projectile_applies_direct_damage_then_Burning')
            phase('impact_dot');return
        if name=='impact_dot':
            if age<3.1:return
            t=targets['hit'];lethal=targets['lethal_hit']
            assert health(t)==34 and damage_ticks(t)==3 and prop(t['actor'],'DamageEvents')==4
            assert not running(t) and not actions(t)
            assert prop(t['actor'],'LastSource') is None and prop(t['actor'],'LastController') is None
            assert abs(t['system'].call_method('GetAttributeValue',args=(tag('Attribute.Rage'),))-49.5)<.001
            assert prop(lethal['actor'],'DamageEvents')==1 and not actions(lethal)
            s['checks']+=['Burning_outlives_projectile_and_preserves_native_Rage','lethal_projectile_cleans_effect_before_first_period']
            pending=target(10);pending['effect']=grant(pending);targets['pending']=pending
            assert running(pending) and damage_ticks(pending)==0
            s['checks'].append('EndPIE_with_pending_Burning_timer')
            finish()
    except Exception:finish(traceback.format_exc())
    finally:s['busy']=False

def verify_teardown():
    pending=s['targets'].get('pending')
    if pending and alive(pending['effect']):
        assert not running(pending)
        assert prop(pending['effect'],'Stops')==1 and damage_ticks(pending)==0

s['handle']=unreal.register_slate_post_tick_callback(tick)
