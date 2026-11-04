"""Real native BehaviorTree/EQS scheduler calling DAS tasks and conditions."""
import json,time,traceback
from pathlib import Path
import unreal
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
player=unreal.GameplayStatics.get_player_controller(world,0)
enemy_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueAICharacter.BP_RogueAICharacter_C')
enemy=next(iter(unreal.GameplayStatics.get_all_actors_of_class(world,enemy_kind)))
controller=enemy.get_controller()
assert controller and controller.get_class().get_name()=='BP_RogueBehaviorController_C'
system=enemy.get_editor_property('ActionSystem')
attributes=enemy.get_editor_property('Attributes')
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
probe.call_method('ConfigureHealth',args=(pawn.get_editor_property('Attributes'),10000.0))
pawn.set_actor_location(unreal.Vector(600,-1500,96),False,True)
pawn.get_editor_property('character_movement').disable_movement()
point_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RoguePatrolPoint.BP_RoguePatrolPoint_C')
points=list(unreal.GameplayStatics.get_all_actors_of_class(world,point_kind))
assert len(points)==4
for point in points:assert point.call_method('RebuildConnections',args=(points,))
low_kind=unreal.load_class(None,'/Game/DasRogue/AI/BT/BP_RogueBTLowHealth.BP_RogueBTLowHealth_C')
brain=controller.get_editor_property('brain_component')
assert brain and brain.get_class().get_name()=='BehaviorTreeComponent'
board=controller.get_editor_property('blackboard')
assert board
low=next(n for n in unreal.ObjectIterator(low_kind) if n.get_outer()==brain)

def now():return unreal.GameplayStatics.get_time_seconds(world)
def prop(obj,name):return obj.get_editor_property(name)
def tag(name):
    value=unreal.GameplayTag();assert value.import_text(name);return value
def health():return prop(attributes,'Health')
def change(value):system.call_method('ApplyAttributeChange',args=(tag('Attribute.Health'),float(value-health())))
def condition():return low.call_method('PerformConditionCheckAI',args=(controller,enemy))

probe.call_method('ConfigureHealth',args=(attributes,300.0))
maximum=prop(attributes,'HealthMax')
assert maximum==300.0
change(90);assert not condition(),'30 percent must not pass strict LowHealth condition'
change(89);assert condition()
change(300)
result=Path(unreal.Paths.project_saved_dir())/'Tests/rogue_behavior_tree_pie.json'
s={'phase':'patrol','at':now(),'started':time.perf_counter(),'done':False,'checks':['native_BT_and_blackboard_created','strict_low_health_threshold_30_percent'],
   'origin':enemy.get_actor_location(),'maximum':maximum}

def phase(name):s.update(phase=name,at=now())
def check(name):
    if name not in s['checks']:s['checks'].append(name)
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks'],
        'phase':s['phase'],'health':health(),'position':str(enemy.get_actor_location()),
        'sight_events':prop(controller,'SightEvents'),'hearing_events':prop(controller,'HearingEvents'),
        'perceived':[str(a) for a in prop(controller,'Perception').get_currently_perceived_actors(None)],
        'target':str(board.get_value_as_object('TargetActor')),'brain_running':brain.is_running(),'brain_paused':brain.is_paused()},indent=2))

def tick(delta):
    if s['done'] or s.get('busy'):return
    s['busy']=True
    try:
        assert time.perf_counter()-s['started']<140,'Behavior test timeout: '+s['phase']
        age=now()-s['at']
        # Keep a real perceived threat during the long cooldown/cover test.
        if s['phase'] in ('cover','stun','resume','cooldown','heal_again') and now()>=s.get('next_noise',0):
            unreal.AISense_Hearing.report_noise_event(world,pawn.get_actor_location(),3.0,pawn,0.0,'BT_regression')
            s['next_noise']=now()+.5
        if s['phase']=='patrol':
            assert brain.is_running(),'Native tree did not start'
            if (enemy.get_actor_location()-s['origin']).length()<80:
                assert age<5,'Native BT patrol task did not move';return
            assert board.get_value_as_object('CurrentPatrolPoint') in points
            check('DAS_FindPatrol_and_native_MoveTo_on_Recast')
            # Clear route, enter an unobstructed native sight corridor.
            enemy.set_actor_location(unreal.Vector(4400,600,96),False,True)
            enemy.set_actor_rotation(unreal.Rotator(0,-90,0),True)
            pawn.set_actor_location(unreal.Vector(4400,-200,96),False,True)
            s['hp']=prop(pawn.get_editor_property('Attributes'),'Health')
            unreal.AISense_Hearing.report_noise_event(world,pawn.get_actor_location(),3.0,pawn,0.0,'BT_regression')
            phase('target');return
        if s['phase']=='target':
            if board.get_value_as_object('TargetActor')!=pawn:
                unreal.AISense_Hearing.report_noise_event(world,pawn.get_actor_location(),3.0,pawn,0.0,'BT_regression')
                assert age<5,'Native EQS did not select perceived player';return
            check('native_PerceivedActors_EQS_selects_target')
            if prop(pawn.get_editor_property('Attributes'),'Health')>=s['hp']:
                assert age<7,'DAS RangedAttack task did not damage player';return
            assert board.get_value_as_bool('WithinRange')
            check('DAS_CheckRange_and_RangedAttack_native_damage')
            change(60)
            s['low_at']=now();s['low_position']=enemy.get_actor_location()
            phase('cover');return
        if s['phase']=='cover':
            if health()<=60:
                assert age<14,'Cover/EQS/HealSelf did not complete';return
            assert health()==160,'HealSelf must add 100, not fill all health'
            context_kind=unreal.load_class(None,'/Game/DasRogue/AI/BT/BP_RogueEQSTarget.BP_RogueEQSTarget_C')
            contexts=[n for n in unreal.ObjectIterator(context_kind) if n.get_outer().get_class().get_name()=='EnvQueryManager']
            assert len(contexts)==1
            provided=contexts[0].call_method('ProvideSingleActor',args=(enemy,enemy))
            if isinstance(provided,tuple):provided=provided[-1]
            assert provided==pawn,('DAS const/out EQS context returned a different actor: '+str(provided))
            assert enemy not in prop(controller,'Perception').get_currently_perceived_actors(None),'Native perception includes its own friendly pawn'
            check('world_owned_EQS_context_dispatches_const_out_actor')
            assert (enemy.get_actor_location()-s['low_position']).length()>100,'No cover movement occurred'
            assert now()-s['low_at']>1,'Healing skipped the wait before HealSelf'
            check('EQS_cover_native_path_wait_and_DAS_HealSelf_100')
            change(60)
            s['cooldown_at']=now()
            stun_kind=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionEffectStun.BP_RogueActionEffectStun_C')
            assert stun_kind
            s['effect']=system.call_method('GrantAction',args=(stun_kind,))
            assert s['effect']
            s['stun_origin']=enemy.get_actor_location()
            phase('stun');return
        if s['phase']=='stun':
            if age<.3:return
            assert brain.is_paused(),'Native BT brain was not paused by stun'
            assert (enemy.get_actor_location()-s['stun_origin']).length()<10
            assert health()==60,'Healing bypassed cooldown/stun'
            check('stun_pauses_native_brain_and_movement')
            system.call_method('RemoveAction',args=(s['effect'],))
            phase('resume');return
        if s['phase']=='resume':
            if age<.3:return
            assert not brain.is_paused() and brain.is_running()
            check('removing_stun_resumes_native_tree')
            phase('cooldown');return
        if s['phase']=='cooldown':
            elapsed=now()-s['cooldown_at']
            if elapsed<18:
                assert health()==60,'Heal branch ignored original 20-second cooldown';return
            check('heal_branch_cooldown_blocks_reentry')
            phase('heal_again');return
        if s['phase']=='heal_again':
            if health()<=60:
                assert age<14,'Heal branch did not become available after cooldown';return
            assert health()==160
            check('heal_branch_reenters_after_cooldown')
            change(0)
            phase('death');return
        if s['phase']=='death':
            if age<.2:return
            assert prop(enemy,'Dead') and not brain.is_running()
            check('death_stops_native_brain')
            minion_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueBehaviorMinion.BP_RogueBehaviorMinion_C')
            assert minion_kind
            s['live']=probe.call_method('Spawn',args=(minion_kind,unreal.Vector(4400,600,96),unreal.Rotator()))
            assert s['live']
            phase('live_teardown');return
        if s['phase']=='live_teardown':
            if age<.3:return
            live_brain=s['live'].get_controller().get_editor_property('brain_component')
            assert live_brain and live_brain.is_running()
            check('EndPIE_with_live_native_tree_and_EQS_services')
            finish();return
    except Exception:finish(traceback.format_exc())
    finally:s['busy']=False
s['handle']=unreal.register_slate_post_tick_callback(tick)

def verify_teardown():
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
