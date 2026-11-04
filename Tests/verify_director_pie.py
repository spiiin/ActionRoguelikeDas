"""Native EQS and asynchronous profiles drive real DAS waves on a Recast map."""
import json,time,traceback,unreal
from pathlib import Path
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
director=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueSpawnDirector_C')
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
pawn.set_actor_enable_collision(False)
pawn.get_editor_property('character_movement').disable_movement()
def prop(o,n):return o.get_editor_property(n)
def now():return unreal.GameplayStatics.get_time_seconds(world)
def alive(o):
    try:return o is not None and unreal.SystemLibrary.is_valid(o)
    except TypeError:return False
def tag(n):
    t=unreal.GameplayTag();assert t.import_text(n);return t
def call(n,*args):return director.call_method(n,args=args)
def live():return call('AliveCount')
def monsters():return list(prop(prop(director,'Spawner'),'SpawnedMonsters'))
def pause():call('SetEnabled',False)
def configure(configs,seed=42,limit=2):
    call('Configure',configs,seed,limit)
    call('SetEnabled',True)
config=unreal.load_asset('/Game/DasRogue/Director/DA_Director')
empty_query=unreal.load_asset('/Game/DasRogue/Director/EQS_DirectorEmpty')
def copy_config():
    result=unreal.new_object(config.get_class(),outer=director)
    for name in ['DisplayName','MonsterSpawnTable','SpawnLocationQuery','CreditGainCurve','CreditsPerSecond','StartingCredits','TickInterval','TimeBetweenWaves']:
        result.set_editor_property(name,prop(config,name))
    result.set_editor_property('TimeBetweenWaves',.3)
    return result
pause()
test_config=copy_config()
test_config.set_editor_property('StartingCredits',50.0)
test_config.set_editor_property('TickInterval',.1)
configure([test_config,test_config])
slots=list(prop(director,'Slots'));assert len(slots)==2
seeds=[prop(slot,'InitialSeed') for slot in slots]
assert seeds[0]!=seeds[1]
assert all(len(prop(slot,'Options'))==2 for slot in slots)
s={'done':False,'phase':'cap','at':now(),'started':time.perf_counter(),'checks':['independent_slot_seeds_and_zero_weight_rows_filtered']}
base=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
wrong=unreal.load_class(None,'/Game/DasRogue/BP_RogueCharacter.BP_RogueCharacter_C')
derived=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueBehaviorMinion.BP_RogueBehaviorMinion_C')
assert base.call_method('RejectAIClass',args=(wrong,))
assert not base.call_method('RejectAIClass',args=(derived,))
s['checks'].append('typed_class_accepts_authored_descendant_but_rejects_unrelated_same_native_base')
result=Path(unreal.Paths.project_saved_dir())/'Tests/rogue_director_pie.json'
def phase(n):s['phase']=n;s['at']=now()
def check(n):s['checks'].append(n)
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks']},indent=2))
def tick(delta):
    if s['done']:return
    try:
        assert time.perf_counter()-s['started']<70,'Director scenario timeout: '+s['phase']
        age=now()-s['at']
        if s['phase']=='cap':
            assert live()+len(prop(director,'Reservations'))<=2,'Pending EQS/load overshot the cap'
            if live()<2:
                assert age<8,[(prop(x,'Failures'),prop(x,'Pending'),prop(x,'Credits')) for x in slots]
                return
            s['original_monsters']=monsters()
            assert len(s['original_monsters'])==2
            assert all(prop(m,'MonsterData') and prop(m,'DataActionsGranted')==1 for m in monsters())
            assert all(m.get_controller() for m in monsters())
            # The harness already verifies a complete detouring Recast path before PIE.
            # Calling the static NavigationSystem UFunction during PIE enters its CDO
            # GetWorld() in UE editor instrumentation, which asserts on the native CDO.
            check('native_EQS_async_profile_load_and_data_driven_pawns_with_native_controllers')
            check('two_directors_share_alive_plus_inflight_cap')
            for slot in slots:
                stream=prop(slot,'InitialSeed')
                selected=None
                for _ in range(prop(slot,'Selections')):
                    sample=unreal.DasRandomLibrary.random_float_in_range(stream,0.0,4.0)
                    weight=next(x for x in sample if isinstance(x,float))
                    stream=next(x for x in sample if isinstance(x,int))
                    selected='Grunt' if weight<=3.0 else 'Heavy'
                assert prop(slot,'Seed')==stream and prop(slot,'LastSelectedRow')==selected
            check('weighted_choices_and_mutable_seed_match_native_FRandomStream')
            unreal.SystemLibrary.collect_garbage()
            assert all(alive(x) for x in slots) and all(alive(x) for x in monsters())
            check('slots_and_spawned_monsters_survive_GC')
            pause();s['spawned_before_pause']=prop(director,'TotalSpawned')
            phase('paused');return
        if s['phase']=='paused':
            if age<.4:return
            assert prop(director,'TotalSpawned')==s['spawned_before_pause'] and not prop(director,'Reservations')
            check('pause_cancels_inflight_work_and_prevents_late_spawns')
            victim=monsters()[0]
            prop(victim,'ActionSystem').call_method('ApplyAttributeChange',args=(tag('Attribute.Health'),-10000.0))
            assert prop(victim,'Dead') and live()==1
            call('SetEnabled',True)
            phase('replacement');return
        if s['phase']=='replacement':
            if live()<2:
                assert age<5;return
            assert prop(director,'TotalSpawned')==s['spawned_before_pause']+1
            check('dead_monster_releases_capacity_before_corpse_expiry')
            pause()
            call('Configure',[test_config,test_config],42,2)
            assert [prop(x,'InitialSeed') for x in prop(director,'Slots')]==seeds
            assert live()==0
            check('reconfigure_reseeds_reproducibly_and_cleans_old_pawns')
            bad=copy_config();bad.set_editor_property('SpawnLocationQuery',empty_query)
            bad.set_editor_property('CreditGainCurve',None);bad.set_editor_property('CreditsPerSecond',0.0)
            bad.set_editor_property('StartingCredits',20.0)
            s['bad']=bad
            configure([bad],seed=81,limit=1)
            s['slot']=prop(director,'Slots')[0]
            phase('query_failure');return
        if s['phase']=='query_failure':
            slot=s['slot']
            if prop(slot,'Failures')<1:
                assert age<5;return
            pause()
            assert live()==0 and not prop(director,'Reservations') and abs(prop(slot,'Credits')-20)<.01
            assert not prop(slot,'Pending')
            check('failed_native_EQS_refunds_reserved_budget_and_slot')
            poor=copy_config();poor.set_editor_property('CreditGainCurve',None);poor.set_editor_property('CreditsPerSecond',0.0);poor.set_editor_property('StartingCredits',0.0)
            configure([poor],limit=1);s['slot']=prop(director,'Slots')[0]
            phase('unaffordable');return
        if s['phase']=='unaffordable':
            slot=s['slot']
            if prop(slot,'Unaffordable')<1:
                assert age<2;return
            assert not prop(slot,'Pending') and not prop(director,'Reservations') and live()==0
            check('insufficient_budget_uses_wave_pause_without_starting_a_query')
            pause();s['slot_credits']=prop(slot,'Credits')
            income=copy_config();income.set_editor_property('StartingCredits',0.0);income.set_editor_property('TimeBetweenWaves',10.0)
            configure([income],limit=0);s['slot']=prop(director,'Slots')[0]
            phase('income');return
        if s['phase']=='income':
            if age<.5:return
            assert prop(s['slot'],'Credits')>3 and prop(s['slot'],'CapBlocks')>0
            check('native_float_curve_accrues_credits_even_while_bot_cap_blocks_spawning')
            configure([test_config],seed=2026,limit=1)
            # Stop immediately after scheduling from DAS, before EQS can finish.
            slot=prop(director,'Slots')[0]
            slot.call_method('Step',args=(now(),0.0))
            assert prop(slot,'Pending') and prop(slot,'Query')
            s['cancelled_query']=prop(slot,'Query')
            pause()
            assert not prop(slot,'Pending') and not prop(director,'Reservations')
            assert abs(prop(slot,'Credits')-50)<.01
            check('explicit_pause_aborts_native_EQS_and_refunds_the_request')
            phase('cancelled');return
        if s['phase']=='cancelled':
            if age<.4:return
            assert live()==0
            configure([test_config],seed=51,limit=1)
            slot=prop(director,'Slots')[0];slot.call_method('Step',args=(now(),0.0))
            assert prop(slot,'Pending')
            director.destroy_actor()
            check('EndPlay_cancels_a_live_native_query_and_owned_runtime_slots')
            phase('destroyed');return
        if s['phase']=='destroyed':
            if age<.4:return
            assert all(not alive(m) for m in s['original_monsters'])
            finish()
    except Exception:finish(traceback.format_exc())
s['handle']=unreal.register_slate_post_tick_callback(tick)
