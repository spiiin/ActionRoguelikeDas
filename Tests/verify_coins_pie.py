"""Real WorldSubsystem ticks, batched native ISM IDs, pickup, and AI death loot."""
from pathlib import Path
import json,time,traceback
import unreal

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
player=unreal.GameplayStatics.get_player_controller(world,0)
base_probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueCoinProbe.BP_RogueCoinProbe_C')
probe=base_probe.call_method('Spawn',args=(kind,unreal.Vector(0,0,400),unreal.Rotator()))
assert probe
coins=probe.call_method('Coins')
assert coins and coins.get_outer()==world
probe.call_method('SetCollect',args=(False,))
pawn.get_editor_property('character_movement').disable_movement()
pawn.set_actor_location(unreal.Vector(600,-1500,96),False,True)
enemy_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueAICharacter.BP_RogueAICharacter_C')
for enemy in unreal.GameplayStatics.get_all_actors_of_class(world,enemy_kind):
    controller=enemy.get_controller()
    if controller:controller.destroy_actor()
    enemy.destroy_actor()
extras=[]

def hud_text(player,name):
    hud=player.get_editor_property('HUD')
    widget=hud.get_editor_property('HUD')
    assert widget and widget.is_in_viewport()
    tree=next(t for t in unreal.ObjectIterator(unreal.load_class(None,'/Script/UMG.WidgetTree')) if t.get_outer()==widget)
    return str(unreal.find_object(tree,name).get_text())

def is_live(obj):
    try:
        return unreal.SystemLibrary.is_valid(obj)
    except TypeError as error:
        # UE 5.8 invalidates the UObject inside retained Python wrappers at EndPIE.
        if isinstance(obj,unreal.Object) and 'NativizeObject: Cannot nativize' in str(error):
            return False
        raise

def prop(obj,name):return obj.get_editor_property(name)
def now():return unreal.GameplayStatics.get_time_seconds(world)
def tag(name):
    value=unreal.GameplayTag();assert value.import_text(name);return value
def currency():return prop(prop(pawn,'ActionSystem'),'Coins')
def spawn(kind,location):
    actor=base_probe.call_method('Spawn',args=(kind,location,unreal.Rotator()))
    assert actor;extras.append(actor);return actor
def count():return prop(coins,'CoinCount')
def value():return prop(coins,'RemainingValue')
def validate_instances():
    mesh=prop(coins,'WorldISM')
    assert mesh and mesh.get_owner() is None and mesh.get_outer()==world
    assert mesh.get_instance_count()==count()
    if mesh not in s['renderers']:s['renderers'].append(mesh)
    ids=[]
    for i in range(count()):
        id=coins.call_method('MeshIdAt',args=(i,));ids.append(id)
        index=probe.call_method('InstanceIndex',args=(id,))
        assert 0<=index<mesh.get_instance_count()
        transform=mesh.get_instance_transform(index,True)
        expected=coins.call_method('LocationAt',args=(i,))+prop(coins,'VisualOffset')
        assert (transform.translation-expected).length()<.01
    assert len(ids)==len(set(ids))

result=Path(unreal.Paths.project_saved_dir())/'Tests/rogue_coins_pie.json'
s={'phase':'setup','at':now(),'started':time.perf_counter(),'done':False,'checks':[], 'renderers':[]}
def phase(name):s.update(phase=name,at=now())
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    for actor in [probe,*extras]:
        if is_live(actor):
            if isinstance(actor,unreal.Pawn):
                owner=actor.get_controller()
                if owner:owner.destroy_actor()
            actor.destroy_actor()
    result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks']},indent=2))

def tick(delta):
    if s['done'] or s.get('busy'):return
    s['busy']=True
    try:
        assert time.perf_counter()-s['started']<60,s['phase']
        for obj in [coins,probe,pawn,player,*extras]:
            if is_live(obj):assert not prop(obj,'LastDasError'),prop(obj,'LastDasError')
        state=s['phase'];age=now()-s['at']
        if state=='setup':
            if age<.2:return
            assert prop(coins,'Accepting') and count()==0 and value()==0 and currency()==0
            assert probe.call_method('Coins')==coins and prop(coins,'WorldISM')
            validate_instances()
            sound=unreal.load_asset('/Engine/EditorSounds/Notifications/CompileSuccess')
            assert sound
            coins.set_editor_property('CoinSound',sound)
            s['checks'].append('world_collection_owns_one_renderer_without_coin_actors')
            draws=list(probe.call_method('RandomSequence',args=(123,)))
            # Golden sequence for FRandomStream(123).RandRange(1,15), UE RandomStream.h.
            assert draws==[13,5,8,7,12,3],draws
            assert draws==list(probe.call_method('RandomSequence',args=(123,)))
            s['checks'].append('script_seed_advances_native_FRandomStream_reproducibly')
            locations=[unreal.Vector(3200,0,10),unreal.Vector(4400,0,10),unreal.Vector(3240,0,10),unreal.Vector(3280,0,10),unreal.Vector(4400,1200,10)]
            assert not coins.call_method('AddCoinPickups',args=(locations,[1]))
            assert not coins.call_method('AddCoinPickups',args=([locations[0]],[0]))
            assert not coins.call_method('AddCoinPickups',args=([locations[0]],[-3]))
            assert coins.call_method('AddCoinPickups',args=([],[])) and count()==0
            assert coins.call_method('AddCoinPickups',args=(locations,[2,3,5,7,11]))
            assert count()==5 and value()==28
            validate_instances()
            s['checks'].append('validated_bulk_add_is_atomic_and_preserves_values')
            removed=coins.call_method('MeshIdAt',args=(1,));last=coins.call_method('MeshIdAt',args=(4,))
            assert not probe.call_method('InvalidNativeRemoval',args=(last,))
            assert not coins.call_method('RemoveCoinPickup',args=(-1,))
            assert coins.call_method('RemoveCoinPickup',args=(1,))
            assert count()==4 and value()==25 and coins.call_method('MeshIdAt',args=(1,))==last
            assert probe.call_method('InstanceIndex',args=(removed,))==-1
            validate_instances()
            unreal.SystemLibrary.collect_garbage()
            validate_instances()
            s['checks'].append('swap_removal_keeps_stable_id_mapping_and_gc_retains_renderer')
            pawn.set_actor_location(unreal.Vector(3240,0,96),False,True)
            probe.call_method('SetCollect',args=(True,));phase('pickup');return
        if state=='pickup':
            if count()==4:
                assert age<1,'WorldSubsystem Tick did not collect';return
            assert count()==1 and value()==11 and currency()==14
            assert prop(coins,'GrantCalls')==1 and prop(coins,'CollectedValue')==14
            validate_instances()
            s['checks'].append('real_subsystem_tick_collects_three_coins_with_one_summed_grant')
            audio=prop(coins,'WorldAudio')
            assert audio and audio.get_outer()==world and audio.get_owner() is None
            s['renderers'].append(audio)
            unreal.SystemLibrary.collect_garbage()
            assert is_live(audio)
            s['checks'].append('native_audio_trigger_and_strong_world_audio_ownership')
            probe.call_method('SetHealth',args=(pawn,0.0))
            pawn.set_actor_location(unreal.Vector(4400,1200,96),False,True)
            phase('dead');return
        if state=='dead':
            if age<.2:return
            assert count()==1 and currency()==14
            probe.call_method('SetCollect',args=(False,))
            probe.call_method('SetHealth',args=(pawn,100.0))
            pawn.set_actor_location(unreal.Vector(600,-1500,96),False,True)
            player.call_method('UnPossess',args=())
            assert coins.call_method('AddCoinPickups',args=([unreal.Vector(0,0,0)],[1]))
            probe.call_method('SetCollect',args=(True,));phase('unpossessed');return
        if state=='unpossessed':
            if age<.2:return
            assert count()==2 and value()==12
            probe.call_method('SetCollect',args=(False,));player.possess(pawn)
            s['checks'].append('dead_or_missing_player_does_not_consume_or_lose_coins')
            generator=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueCoinTestActor_C')
            assert generator.call_method('SpawnCoins',args=(3,))
            assert count()==5 and value()==42
            validate_instances()
            s['checks'].append('demo_generator_adds_a_batch_through_the_same_world_service')
            enemy=spawn(enemy_kind,unreal.Vector(3200,1200,96));s['enemy']=enemy
            data=unreal.load_asset('/Game/DasRogue/AI/DA_LootRegression')
            probe.call_method('ConfigureEnemy',args=(enemy,data))
            s['before_count']=count();s['before_value']=value()
            unreal.GameplayStatics.apply_damage(enemy,1000.0,player,pawn,None)
            phase('loot');return
        if state=='loot':
            enemy=s['enemy']
            if not prop(enemy,'Dead'):
                assert age<1;return
            assert prop(enemy,'LootDrops')==1 and prop(enemy,'LastLootCoins')==37
            assert value()==s['before_value']+37
            new_total=0
            for index in range(s['before_count'],count()):
                amount=coins.call_method('AmountAt',args=(index,));new_total+=amount
                assert 1<=amount<=15
                location=coins.call_method('LocationAt',args=(index,))
                offset=location-enemy.get_actor_location()
                assert offset.x*offset.x+offset.y*offset.y<=251*251
            assert new_total==37
            validate_instances()
            s['drop_value']=value();s['drop_count']=count()
            probe.call_method('RepeatDrop',args=(enemy,))
            unreal.GameplayStatics.apply_damage(enemy,1000.0,player,pawn,None)
            phase('single_drop');return
        if state=='single_drop':
            if age<.2:return
            assert count()==s['drop_count'] and value()==s['drop_value']
            s['checks'].append('native_lethal_damage_drops_monster_data_value_once_in_bounded_positive_coins')
            phase('expiry');return
        if state=='expiry':
            if is_live(s['enemy']):
                assert age<3;return
            assert value()==s['drop_value'] and count()==s['drop_count']
            validate_instances()
            s['checks'].append('loot_outlives_its_dead_owner_and_preserves_ism_alignment')
            # No MonsterData uses the original default ten-credit reward.
            # Spawn outside navigation to force placement fallback without losing value.
            enemy=spawn(enemy_kind,unreal.Vector(1000000,1000000,96));s['enemy']=enemy
            probe.call_method('ConfigureEnemy',args=(enemy,None))
            s['before_count']=count();s['before_value']=value()
            unreal.GameplayStatics.apply_damage(enemy,1000.0,player,pawn,None)
            phase('fallback');return
        if state=='fallback':
            enemy=s['enemy']
            if not prop(enemy,'Dead'):
                assert age<1;return
            assert prop(enemy,'LootDrops')==1 and prop(enemy,'LastLootCoins')==10
            assert value()==s['before_value']+10 and count()>s['before_count']
            action=prop(enemy,'ActionSystem').call_method('FindAction',args=(tag('Action.DropLoot'),))
            assert prop(action,'PlacementFallbacks')==prop(action,'DroppedCoins')>0
            for index in range(s['before_count'],count()):
                assert (coins.call_method('LocationAt',args=(index,))-enemy.get_actor_location()).length()<.01
            validate_instances()
            s['checks'].append('default_reward_and_failed_nav_query_preserve_all_ten_credits')
            data=unreal.load_asset('/Game/DasRogue/AI/DA_LootRegression')
            data.set_editor_property('LootCoins',0)
            enemy=spawn(enemy_kind,unreal.Vector(3500,1200,96));s['enemy']=enemy
            probe.call_method('ConfigureEnemy',args=(enemy,data))
            s['before_count']=count();s['before_value']=value()
            unreal.GameplayStatics.apply_damage(enemy,1000.0,player,pawn,None)
            phase('zero');return
        if state=='zero':
            enemy=s['enemy']
            if not prop(enemy,'Dead'):
                assert age<1;return
            assert prop(enemy,'LootDrops')==1 and prop(enemy,'LastLootCoins')==0
            assert count()==s['before_count'] and value()==s['before_value']
            unreal.load_asset('/Game/DasRogue/AI/DA_LootRegression').set_editor_property('LootCoins',37)
            s['checks'].append('zero_reward_creates_no_zero_value_instances')
            wallet=prop(pawn,'ActionSystem')
            before=currency()
            assert wallet.call_method('GrantCoins',args=(9007199254740993,))
            assert currency()==before+9007199254740993
            assert not wallet.call_method('GrantCoins',args=(-1,))
            assert not wallet.call_method('GrantCoins',args=(9223372036854775807,))
            assert currency()==before+9007199254740993
            s['checks'].append('int64_wallet_keeps_exact_large_grants_and_rejects_overflow')
            phase('wallet_hud');return
        if state=='wallet_hud':
            if age<.2:return
            text=hud_text(player,'CoinsText')
            assert str(currency()) in text,text
            s['checks'].append('int64_balance_event_refreshes_HUD_without_rounding')
            finish()
    except Exception:finish(traceback.format_exc())
    finally:s['busy']=False

s['handle']=unreal.register_slate_post_tick_callback(tick)


def verify_teardown():
    """Called by the harness after EndPIE, while Python still retains wrappers."""
    assert not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    for mesh in s['renderers']:
        assert not is_live(mesh), 'World renderer survived EndPIE'
    if is_live(coins):
        assert not prop(coins,'Accepting') and prop(coins,'CoinCount')==0
        assert not prop(coins,'WorldISM') and not prop(coins,'WorldAudio')
    receipt=json.loads(result.read_text())
    if receipt['passed']:
        receipt['checks'].append('EndPIE_destroys_world_renderer_and_clears_subsystem')
        result.write_text(json.dumps(receipt,indent=2))
