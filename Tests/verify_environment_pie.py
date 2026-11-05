"""Exercise real input, multicast delivery and native tick/projectile movement in PIE."""
from pathlib import Path
import unreal,json,time,traceback,math
ROOT=Path(__file__).resolve().parents[1]
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
def prop(obj,key):return obj.get_editor_property(key)
def now():return unreal.GameplayStatics.get_time_seconds(world)
def find(name):return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()==name)
lever=find('BP_RogueLeverDemo_C')
spammer=find('BP_RogueProjectileSpammer_C')
link=find('BP_RogueLeverSpammerDemo_C')
player=unreal.GameplayStatics.get_player_controller(world,0)
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
pawn.character_movement.disable_movement()
inputs=max([v for v in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if v.get_outer().get_class().get_name()=='LocalPlayer'],key=lambda v:int(v.get_outer().get_name().rsplit('_',1)[-1]))
action=unreal.load_asset('/Game/DasRogue/Input/IA_Interact')
def press():inputs.inject_input_vector_for_action(action,unreal.Vector(1,0,0),[],[])
def length(v):return math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z)
def dot(a,b):return a.x*b.x+a.y*b.y+a.z*b.z
s=dict(done=False,phase='idle',at=now(),started=time.perf_counter(),checks=[])
def phase(name):s['phase']=name;s['at']=now()
def check(name):s['checks'].append(name)
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    (ROOT/'Saved/Tests/rogue_environment_pie.json').write_text(json.dumps(dict(passed=error is None,error=error,checks=s['checks']),indent=2))
def tick(delta):
    if s['done']:return
    try:
        assert time.perf_counter()-s['started']<35,s['phase']
        for actor in [lever,spammer,link,player]:
            if unreal.SystemLibrary.is_valid(actor):assert not prop(actor,'LastDasError'),prop(actor,'LastDasError')
        age=now()-s['at']
        if s['phase']=='idle':
            if age<.7:return
            assert isinstance(spammer,unreal.Pawn)
            assert not prop(spammer,'Spawning') and prop(spammer,'ProjectilesSpawned')==0
            assert not spammer.is_actor_tick_enabled(), 'Spammer native tick should start disabled'
            assert abs(spammer.get_actor_tick_interval()-.5)<.001
            assert prop(lever,'Pulls')==0 and prop(link,'Activations')==0
            check('original_Pawn_base_half_second_interval_and_disabled_start')
            s['presses']=prop(player,'InteractPresses');s['successes']=prop(player,'SuccessfulInteractions')
            press();phase('first_press');return
        if s['phase']=='first_press':
            if age<.1:return
            assert prop(player,'InteractPresses')==s['presses']+1
            assert prop(player,'SuccessfulInteractions')==s['successes']+1
            assert prop(lever,'Pulls')==1 and prop(link,'Activations')==1
            assert prop(spammer,'Spawning')
            check('native_EnhancedInput_E_selects_lever_and_dispatches_typed_multicast_once')
            phase('first_projectile');return
        if s['phase']=='first_projectile':
            if prop(spammer,'ProjectilesSpawned')<1:
                assert age<1.2,'Native actor tick did not spawn';return
            projectile=prop(spammer,'LastProjectile')
            assert unreal.SystemLibrary.is_valid(projectile)
            assert prop(projectile,'instigator')==spammer and projectile.get_owner() is None
            velocity=projectile.get_velocity()
            assert velocity.x>1900 and abs(velocity.y)<1
            check('Undefined_collision_spawn_preserves_spammer_instigator_no_owner_and_native_movement')
            s['count']=prop(spammer,'ProjectilesSpawned');phase('cadence');return
        if s['phase']=='cadence':
            if age<.2:
                assert prop(spammer,'ProjectilesSpawned')==s['count'],'Spawns each frame instead of each native tick';return
            if age<1.05:return
            count=prop(spammer,'ProjectilesSpawned')-s['count']
            assert count==2,('Half-second cadence',count,age)
            check('native_tick_emits_two_projectiles_per_second')
            unreal.SystemLibrary.collect_garbage()
            s['presses']=prop(player,'InteractPresses');press();phase('repeat');return
        if s['phase']=='repeat':
            if age<.15:return
            assert prop(lever,'Pulls')==2 and prop(link,'Activations')==2
            assert prop(player,'InteractPresses')==s['presses']+1
            assert prop(spammer,'Spawning'),'Original start is not a toggle'
            check('repeat_E_broadcasts_again_without_toggling_or_duplicate_binding_after_GC')
            spammer.call_method('StopSpawning',args=())
            s['count']=prop(spammer,'ProjectilesSpawned');phase('stopped');return
        if s['phase']=='stopped':
            if age<.7:return
            assert prop(spammer,'ProjectilesSpawned')==s['count'] and not spammer.is_actor_tick_enabled()
            check('explicit_stop_disables_native_tick_without_removing_existing_projectiles')
            spammer.set_actor_rotation(unreal.Rotator(0,90,0),False)
            arrow=prop(spammer,'Arrow')
            arrow.set_relative_location(unreal.Vector(100,40,20),False,True)
            arrow.set_relative_rotation(unreal.Rotator(0,30,0),False,True)
            arrow.set_relative_scale3d(unreal.Vector(1.3,.8,1.1))
            s['arrow']=arrow;s['count']=prop(spammer,'ProjectilesSpawned')
            spammer.call_method('StartSpawning',args=());phase('transformed');return
        if s['phase']=='transformed':
            if prop(spammer,'ProjectilesSpawned')==s['count']:
                assert age<1.2;return
            projectile=prop(spammer,'LastProjectile');arrow=s['arrow']
            pose=arrow.get_world_transform()
            expected=arrow.get_forward_vector()
            assert dot(projectile.get_actor_forward_vector(),expected)>.9999
            offset=projectile.get_actor_location()-pose.translation
            distance=dot(offset,expected)
            assert -.1<=distance<300,(offset,distance)
            assert length(offset-expected*distance)<.1,('Wrong Arrow origin',offset)
            assert length(projectile.get_actor_scale3d()-pose.scale3d)<.01
            assert dot(projectile.get_velocity(),expected)>1900
            check('Arrow_world_translation_rotation_scale_drive_spawn_and_flight')
            spammer.call_method('StopSpawning',args=())
            spammer.destroy_actor()
            press();phase('missing_spammer');return
        if s['phase']=='missing_spammer':
            if age<.15:return
            assert prop(lever,'Pulls')==3 and prop(link,'Activations')==3
            check('destroyed_spammer_reference_is_ignored_by_live_typed_handler')
            link.destroy_actor()
            press();phase('unbound');return
        if s['phase']=='unbound':
            if age<.15:return
            assert prop(lever,'Pulls')==4
            check('destroying_wiring_unsubscribes_before_next_lever_interaction')
            finish()
    except Exception:finish(traceback.format_exc())
s['handle']=unreal.register_slate_post_tick_callback(tick)
