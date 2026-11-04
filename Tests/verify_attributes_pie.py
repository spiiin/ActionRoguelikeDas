"""Real PIE: attribute arithmetic/policy, damage Rage, ownership and reentrant events."""
import json,time,traceback
from pathlib import Path
import unreal

w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
p=unreal.GameplayStatics.get_player_pawn(w,0)
pc=unreal.GameplayStatics.get_player_controller(w,0)
system=p.get_editor_property('ActionSystem')
health=p.get_editor_property('Attributes')
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_RogueAttributeProbe_C')

def tag(name):
    value=unreal.GameplayTag()
    assert value.import_text('Attribute.'+name)
    return value

def attributes(target=p):
    owner=system if target==p else target.get_editor_property('System')
    return owner.call_method('GetAttributeSet')

def value(name,target=p):return attributes(target).call_method('GetValue',args=(tag(name),))
def base(name,target=p):return attributes(target).call_method('GetBaseValue',args=(tag(name),))
def modifier(name,target=p):return attributes(target).call_method('GetModifierValue',args=(tag(name),))
def change(method,name,amount,target=p):return probe.call_method(method,args=(target,tag(name),amount))
def speed():return p.get_editor_property('character_movement').get_editor_property('max_walk_speed')
def near(actual,expected):assert abs(actual-expected)<.001,(actual,expected)
def watch(target=p):probe.call_method('Watch',args=(target,))

receipt=Path('C:/src/ActionRoguelikeDas/Saved/Tests/rogue_attributes_pie.json')
s={'phase':'initial','at':time.perf_counter(),'started':time.perf_counter(),'checks':[],'done':False,'spawned':[]}
def phase(name):s['phase']=name;s['at']=time.perf_counter()
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    for actor in s['spawned']:
        if unreal.SystemLibrary.is_valid(actor):actor.destroy_actor()
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks'],'elapsed_seconds':time.perf_counter()-s['started']},indent=2),encoding='utf-8')
def tick(delta):
    if s['done']:return
    try:
        assert time.perf_counter()-s['started']<60,'Attribute checks timed out in '+s['phase']
        for obj in (p,system,health,probe):
            assert not obj.get_editor_property('LastDasError'),obj.get_editor_property('LastDasError')
        state=s['phase']
        if state=='initial':
            assert attributes()==health.get_editor_property('AttributeSet')
            assert attributes().get_outer()==health
            near(value('Health'),100);near(value('HealthMax'),100);near(value('Rage'),0)
            near(base('MoveSpeed'),550);near(value('MoveSpeedMultiplier'),1)
            s['checks'].append({'player_set_defaults_shared_with_damage_bridge':True})
            watch()
            assert change('OverrideBase','Rage',10)
            assert change('AddModifier','Rage',5)
            assert change('OverrideBase','Rage',20)
            assert change('AddBase','Rage',2)
            assert change('AddModifier','Rage',-5)
            phase('arithmetic');return
        if state=='arithmetic':
            near(base('Rage'),22);near(modifier('Rage'),0);near(value('Rage'),22)
            assert probe.get_editor_property('RageEvents')==5
            near(probe.get_editor_property('LastOld'),27);near(probe.get_editor_property('LastNew'),22)
            s['checks'].append({'base_modifier_override_and_old_new_notifications':True})
            s['events']=probe.get_editor_property('Events')
            assert not change('AddBase','Rage',float('nan'))
            assert not change('AddModifier','Rage',float('inf'))
            assert not change('OverrideBase','HealthMax',-1)
            assert not change('AddBase','Rage',0)
            other=unreal.GameplayTag();assert other.import_text('Action.PrimaryAttack')
            assert not probe.call_method('AddBase',args=(p,other,10.0))
            phase('invalid');return
        if state=='invalid':
            near(value('Rage'),22);near(value('HealthMax'),100)
            assert probe.get_editor_property('Events')==s['events']
            s['checks'].append({'nonfinite_unknown_negative_max_and_noop_rejected_without_events':True})
            change('OverrideBase','MoveSpeed',300);change('AddModifier','MoveSpeed',50)
            change('AddModifier','MoveSpeedMultiplier',.5)
            near(speed(),525)
            change('OverrideBase','MoveSpeed',400);near(speed(),675)
            change('AddModifier','MoveSpeed',-50);change('AddModifier','MoveSpeedMultiplier',-.5)
            near(speed(),400)
            change('OverrideBase','MoveSpeed',450)
            sprint=unreal.GameplayTag();assert sprint.import_text('Action.Sprint')
            assert system.call_method('StartAction',args=(sprint,));near(speed(),720)
            change('AddBase','MoveSpeed',50);near(speed(),800)
            assert system.call_method('StopAction',args=(sprint,));near(speed(),500)
            change('OverrideBase','MoveSpeed',450)
            s['checks'].append({'movement_product_and_sprint_modifier_preserve_base_changes':True})
            watch();change('OverrideBase','HealthMax',80)
            phase('maximum');return
        if state=='maximum':
            near(value('Health'),80);near(health.get_editor_property('Health'),80)
            near(health.get_editor_property('HealthMax'),80)
            assert probe.get_editor_property('HealthEvents')==1
            s['checks'].append({'lower_max_clamps_health_and_notifies_health_observers':True})
            change('OverrideBase','HealthMax',150)
            phase('maximum_ui');return
        if state=='maximum_ui':
            near(value('Health'),80)
            assert '150' in str(p.get_editor_property('HealthLabel').get_editor_property('text'))
            s['checks'].append({'max_only_changes_refresh_health_ui':True})
            change('OverrideBase','HealthMax',100)
            health.call_method('ApplyHealthChange',args=(p,100.0))
            change('OverrideBase','Rage',0)
            watch()
            unreal.GameplayStatics.apply_damage(p,25.0,pc,probe,None)
            phase('damage');return
        if state=='damage':
            near(value('Health'),75);near(base('Rage'),0);near(modifier('Rage'),18.75)
            assert probe.get_editor_property('HealthEvents')==1 and probe.get_editor_property('RageEvents')==1
            assert probe.get_editor_property('LastInstigator')==probe
            assert '18.75' in str(p.get_editor_property('HealthLabel').get_editor_property('text'))
            s['checks'].append({'native_damage_grants_75_percent_rage_with_source_and_ui_update':True})
            health.call_method('ApplyHealthChange',args=(p,10.0))
            phase('healing');return
        if state=='healing':
            near(value('Health'),85);near(value('Rage'),18.75)
            s['checks'].append({'healing_does_not_generate_rage':True})
            change('AddModifier','Rage',-modifier('Rage'))
            change('OverrideBase','Rage',0)
            watch();probe.set_editor_property('Reenter',True)
            change('OverrideBase','Rage',10)
            phase('reentry');return
        if state=='reentry':
            near(base('Rage'),10);near(modifier('Rage'),1);near(value('Rage'),11)
            assert probe.get_editor_property('Reentered') and probe.get_editor_property('RageEvents')==2
            near(probe.get_editor_property('LastOld'),10);near(probe.get_editor_property('LastNew'),11)
            probe.set_editor_property('Reenter',False)
            s['checks'].append({'reentrant_observer_sees_committed_values':True})
            second=probe.call_method('SpawnCopy',args=(unreal.Vector(-5000,0,200),))
            assert second;s['spawned'].append(second);s['second']=second
            near(value('Rage',second),0)
            change('AddBase','Rage',3,second)
            near(value('Rage',second),3);near(value('Rage'),11)
            probe.call_method('WatchSet',args=(second,))
            unreal.SystemLibrary.collect_garbage()
            phase('ownership');return
        if state=='ownership':
            second=s['second']
            assert probe.call_method('WatchedSetAlive')
            s['checks'].append({'per_owner_values_and_strong_reflected_ownership_survive_gc':True})
            assert probe.call_method('UseMonster',args=(second,))
            assert not attributes(second).call_method('HasAttribute',args=(tag('Rage'),))
            near(value('Health',second),100)
            unreal.SystemLibrary.collect_garbage()
            phase('replacement');return
        if state=='replacement':
            second=s['second']
            assert not probe.call_method('WatchedSetAlive'),'Old set retained after replacement'
            unreal.GameplayStatics.apply_damage(second,10.0,pc,p,None)
            phase('monster_damage');return
        if state=='monster_damage':
            second=s['second']
            near(value('Health',second),90);near(value('Rage',second),0)
            s['checks'].append({'replacement_preserves_shared_values_releases_old_set_and_monster_has_no_rage':True})
            assert probe.call_method('UsePlayer',args=(second,))
            unreal.GameplayStatics.apply_damage(second,200.0,pc,p,None)
            phase('overkill');return
        if state=='overkill':
            second=s['second']
            near(value('Health',second),0);near(value('Rage',second),150)
            s['checks'].append({'overkill_rage_uses_received_damage_before_health_clamp':True})
            finish()
    except Exception:finish(traceback.format_exc())
s['handle']=unreal.register_slate_post_tick_callback(tick)
