"""Fresh PIE. Strong reflected ownership, weak observation, sprint and source Action rules."""
import unreal, time, json, traceback, gc
from pathlib import Path
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert w
p=unreal.GameplayStatics.get_player_pawn(w,0)
pc=unreal.GameplayStatics.get_player_controller(w,0)
system=p.get_editor_property('ActionSystem')
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
movement=p.get_editor_property('character_movement')
base_class=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueAction.BP_RogueAction_C')
assert len(system.get_editor_property('Actions'))==2,'Character must grant sprint and primary attack'
def tag(name):
    result=unreal.GameplayTag()
    assert result.import_text(name), name
    assert str(result.get_editor_property('tag_name'))==name, name
    return result
def tags(*names):
    return unreal.GameplayTagLibrary.make_gameplay_tag_container_from_array([tag(n) for n in names])
def action():return system.call_method('FindAction',args=(tag('Action.Sprint'),))
def speed():return movement.get_editor_property('max_walk_speed')
def collect():
    gc.collect()
    unreal.collect_garbage()
def held_watch():
    a=action()
    assert a.get_outer()==system,'NewObject Outer must be ActionSystem'
    probe.call_method('Watch',args=(a,))
held_watch()
collect()
assert probe.call_method('WatchAlive'),'Reflected Actions failed to keep UObject alive'
assert action().get_outer()==system
checks=[{'strong_reflected_array_survives_gc':True}]
# No UObject is returned to Python; only the weak DAS handle observes this orphan.
probe.call_method('CreateOrphan',args=(base_class,system))
assert probe.call_method('WatchAlive')
collect()
assert not probe.call_method('WatchAlive'),'Outer or a hidden runtime root retained the unowned object'
checks.append({'outer_alone_does_not_retain':True})
def removed_watch():
    a=system.call_method('GrantAction',args=(base_class,))
    probe.call_method('Watch',args=(a,))
    assert system.call_method('RemoveAction',args=(a,))
removed_watch()
collect()
assert not probe.call_method('WatchAlive'),'Removed action retained after all strong references were dropped'
checks.append({'removed_action_collected':True})
gc_receipt=Path('C:/src/ActionRoguelikeDas/Saved/Tests/rogue_actions_gc.json')
gc_receipt.parent.mkdir(parents=True,exist_ok=True)
gc_receipt.write_text(json.dumps({'passed':True,'checks':checks},indent=2),encoding='utf-8')
assert probe.call_method('RejectCreation',args=(unreal.Actor,system))
checks.append({'actor_class_rejected_by_object_factory':True})

sibling=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueUnrelatedObject.BP_RogueUnrelatedObject_C')
assert sibling
assert probe.call_method('RejectTypedCreation',args=(sibling,system))
assert not any(obj.get_outer()==system for obj in unreal.ObjectIterator(sibling)), 'Wrong authored class was constructed before rejection'
assert probe.call_method('RejectTypedCreation',args=(action().get_class(),unreal.get_default_object(system.get_class())))
checks.append({'unrelated_authored_class_rejected_before_construction':True,'template_outer_rejected':True})

# The second Character must own distinct instances, state and modifier values.
second=probe.call_method('Spawn',args=(p.get_class(),unreal.Vector(-350,-350,100),unreal.Rotator()))
second_system=second.get_editor_property('ActionSystem')
assert len(second_system.get_editor_property('Actions'))==2
assert second_system.get_editor_property('Actions')[0]!=action()
assert second_system.call_method('StartAction',args=(tag('Action.Sprint'),))
assert abs(second.get_editor_property('character_movement').get_editor_property('max_walk_speed')-880)<.1
assert abs(speed()-550)<.1
assert second_system.call_method('StopAction',args=(tag('Action.Sprint'),))
checks.append({'per_owner_instances_independent':True})
assert not system.call_method('StartAction',args=(tag('Action.SpecialAttack'),))
def configure_cost():
    a=system.call_method('GrantAction',args=(base_class,))
    a.set_editor_property('ActionName',tag('Action.SecondaryAttack'))
    a.set_editor_property('ActivationCost',{'Attribute.Rage':10.0})
    a.set_editor_property('CooldownTime',.7)
configure_cost()
assert not system.call_method('StartAction',args=(tag('Action.SecondaryAttack'),))
system.call_method('ApplyAttributeChange',args=(tag('Attribute.Rage'),20.0))
assert system.call_method('StartAction',args=(tag('Action.SecondaryAttack'),))
assert not system.call_method('StartAction',args=(tag('Action.SecondaryAttack'),))
assert system.call_method('GetAttributeValue',args=(tag('Attribute.Rage'),))==10.0
assert system.call_method('StopAction',args=(tag('Action.SecondaryAttack'),))
assert not system.call_method('StartAction',args=(tag('Action.SecondaryAttack'),))
checks.append({'cost_once':10,'running_restart_denied':True,'cooldown_after_stop':True})
subsystems=[s for s in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if s.get_outer().get_class().get_name()=='LocalPlayer']
def index(s):
    try:return int(s.get_outer().get_name().rsplit('_',1)[-1])
    except ValueError:return -1
inputs=max(subsystems,key=index)
def inject(name):inputs.inject_input_vector_for_action(unreal.load_asset('/Game/DasRogue/Input/'+name),unreal.Vector(1,0,0),[],[])
old_idle=unreal.SystemLibrary.get_console_variable_int_value('t.IdleWhenNotForeground')
unreal.SystemLibrary.execute_console_command(w,'t.IdleWhenNotForeground 0')
s={'phase':'cooldown','at':time.perf_counter(),'start':time.perf_counter(),'done':False,'checks':checks}
path=Path('C:/src/ActionRoguelikeDas/Saved/Tests/rogue_actions_pie.json')
def phase(name,now):s['phase']=name;s['at']=now
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    if unreal.SystemLibrary.is_valid(second):second.destroy_actor()
    unreal.SystemLibrary.execute_console_command(w,'t.IdleWhenNotForeground '+str(old_idle))
    result={'passed':error is None,'error':error,'checks':s['checks'],'elapsed_seconds':time.perf_counter()-s['start']}
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    unreal.log('DAS_ROGUE_ACTIONS_PIE '+json.dumps(result))
def tick(delta):
    if s['done']:return
    try:
        now=time.perf_counter();age=now-s['at']
        assert now-s['start']<40,'Actions test timeout'
        for obj in [p,pc,system,probe]:assert not obj.get_editor_property('LastDasError'),obj.get_editor_property('LastDasError')
        if s['phase']=='cooldown':
            cost=system.call_method('FindAction',args=(tag('Action.SecondaryAttack'),))
            if cost.call_method('GetCooldownTimeRemaining')>0:return
            assert system.call_method('StartAction',args=(tag('Action.SecondaryAttack'),))
            assert system.call_method('GetAttributeValue',args=(tag('Attribute.Rage'),))==0.0
            assert system.call_method('StopAction',args=(tag('Action.SecondaryAttack'),))
            s['starts']=action().get_editor_property('Starts')
            phase('sprint_hold',now);return
        if s['phase']=='sprint_hold':
            if age<1.0:inject('IA_Sprint');return
            assert action().call_method('IsRunning') and abs(speed()-880)<.1
            assert action().get_editor_property('Starts')==s['starts']+1,'Held Shift repeated Started'
            s['checks'].append({'shift_speed':speed(),'one_start_per_press':True})
            phase('sprint_release',now);return
        if s['phase']=='sprint_release':
            if age<.8:return
            assert not action().call_method('IsRunning') and abs(speed()-550)<.1
            assert system.call_method('StartAction',args=(tag('Action.Sprint'),))
            system.call_method('ApplyAttributeChange',args=(tag('Attribute.MoveSpeedMultiplier'),.5))
            assert abs(speed()-1155)<.1
            system.call_method('AppendActiveTags',args=(tags('StatusEffect.Stunned'),))
            assert not action().call_method('IsRunning') and abs(speed()-825)<.1
            assert not system.call_method('StartAction',args=(tag('Action.Sprint'),))
            system.call_method('RemoveActiveTags',args=(tags('StatusEffect.Stunned'),))
            system.call_method('ApplyAttributeChange',args=(tag('Attribute.MoveSpeedMultiplier'),-.5))
            assert abs(speed()-550)<.1
            s['checks'].append({'stun_cancels_and_blocks_sprint':True,'other_speed_modifier_preserved':True})
            assert system.call_method('StartAction',args=(tag('Action.Sprint'),))
            p.get_editor_property('Attributes').call_method('ApplyHealthChange',args=(p,-100.0))
            phase('death',now);return
        if s['phase']=='death':
            if age<.5:return
            assert p.get_editor_property('Dead')
            assert not system.get_editor_property('Enabled')
            assert not action().call_method('IsRunning') and abs(speed()-550)<.1
            assert not system.call_method('StartAction',args=(tag('Action.Sprint'),))
            s['checks'].append({'death_cancels_actions':True})
            finish()
    except Exception:finish(traceback.format_exc())
s['handle']=unreal.register_slate_post_tick_callback(tick)
print('Actions/GC PIE checks scheduled')
