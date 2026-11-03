"""Enhanced Input E, native pawn overlap, bounded healing and owned respawn timers."""
from pathlib import Path
import json,time,traceback
import unreal

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
player=unreal.GameplayStatics.get_player_controller(world,0)
attributes=pawn.get_editor_property('Attributes')
manual_kind=unreal.load_class(None,'/Game/DasRogue/Pickups/BP_HealthPickupInteract.BP_HealthPickupInteract_C')
auto_kind=unreal.load_class(None,'/Game/DasRogue/Pickups/BP_RogueHealthPickup.BP_RogueHealthPickup_C')
pickup=next(iter(unreal.GameplayStatics.get_all_actors_of_class(world,manual_kind)))
base_probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
probe_kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RoguePickupProbe.BP_RoguePickupProbe_C')
probe=base_probe.call_method('Spawn',args=(probe_kind,unreal.Vector(0,0,400),unreal.Rotator()))
assert probe
subsystems=[v for v in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if v.get_outer().get_class().get_name()=='LocalPlayer']
inputs=max(subsystems,key=lambda v:int(v.get_outer().get_name().rsplit('_',1)[-1]))
interact=unreal.load_asset('/Game/DasRogue/Input/IA_Interact')
extras=[]

def prop(obj,name):return obj.get_editor_property(name)
def now():return unreal.GameplayStatics.get_time_seconds(world)
def health():return prop(attributes,'Health')
def set_health(value):probe.call_method('SetHealth',args=(pawn,value))
def inject():inputs.inject_input_vector_for_action(interact,unreal.Vector(1,0,0),[],[])
def spawn(kind,position):
    actor=base_probe.call_method('Spawn',args=(kind,position,unreal.Rotator()))
    assert actor;extras.append(actor);return actor

pawn.get_editor_property('character_movement').disable_movement()
pawn.set_actor_location(unreal.Vector(1000,-600,96),False,True)
player.set_control_rotation(unreal.Rotator(0,0,0))
pickup.set_actor_location(unreal.Vector(1200,-600,80),False,True)
probe.call_method('SetRespawnDelay',args=(pickup,1.0))
probe.call_method('Arm',args=(pickup,pawn))
assert prop(pickup,'RequireInteraction') and prop(pickup,'Available')
result=Path(unreal.Paths.project_saved_dir())/'Tests/rogue_pickup_pie.json'
s={'phase':'setup','at':now(),'started':time.perf_counter(),'checks':[],'done':False}

def phase(value):s.update(phase=value,at=now())
def finish(error=None):
    s['done']=True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    for actor in [probe,*extras]:
        if unreal.SystemLibrary.is_valid(actor):actor.destroy_actor()
    result.parent.mkdir(parents=True,exist_ok=True)
    result.write_text(json.dumps({'passed':error is None,'error':error,'checks':s['checks']},indent=2))

def tick(delta):
    if s['done'] or s.get('busy'):return
    s['busy']=True
    try:
        assert time.perf_counter()-s['started']<50,s['phase']
        for actor in [pickup,probe,pawn,player,*extras]:
            if unreal.SystemLibrary.is_valid(actor):assert not prop(actor,'LastDasError'),prop(actor,'LastDasError')
        state=s['phase'];age=now()-s['at']
        if state=='setup':
            if age<.2:return
            assert health()==100
            s['presses']=prop(player,'InteractPresses');inject();phase('full');return
        if state=='full':
            if age<.15:return
            assert prop(player,'InteractPresses')==s['presses']+1
            assert prop(player,'InteractionComponent').get_editor_property('SelectedActor')==pickup
            assert prop(pickup,'Available') and prop(pickup,'Collections')==0 and health()==100
            s['checks'].append('real_E_at_full_health_does_not_consume')
            set_health(25);phase('manual_wait');return
        if state=='manual_wait':
            if age<.15:return
            assert health()==25 and prop(pickup,'Collections')==0,'Interaction pickup collected automatically'
            inject();phase('healed');return
        if state=='healed':
            if age<.15:return
            assert health()==75 and prop(pickup,'Collections')==1
            assert prop(probe,'ReentrantAttempts')==1 and not prop(probe,'ReentrantAccepted')
            assert not prop(pickup,'Available') and prop(pickup,'hidden') and not pickup.get_actor_enable_collision()
            s['checks'].append('E_heals_once_and_health_event_reentry_is_rejected')
            inject();phase('inactive');return
        if state=='inactive':
            if age<.15:return
            assert health()==75 and prop(pickup,'Collections')==1
            assert not pickup.call_method('TryCollect',args=(pawn,))
            s['checks'].append('hidden_collision_disabled_and_unavailable_to_repeat_collection')
            phase('respawn');return
        if state=='respawn':
            if not prop(pickup,'Available'):
                assert age<2,'Pickup did not respawn';return
            assert prop(pickup,'Respawns')==1 and not prop(pickup,'hidden') and pickup.get_actor_enable_collision()
            inject();phase('clamped');return
        if state=='clamped':
            if age<.15:return
            assert health()==100 and prop(pickup,'Collections')==2 and prop(probe,'ReentrantAttempts')==2
            assert not prop(probe,'ReentrantAccepted')
            probe.call_method('Arm',args=(None,None))
            s['checks'].append('owned_timer_respawns_and_second_E_clamps_to_health_max')
            phase('second_respawn');return
        if state=='second_respawn':
            if not prop(pickup,'Available'):
                assert age<2;return
            assert prop(pickup,'Respawns')==2
            inject();phase('full_again');return
        if state=='full_again':
            if age<.2:return
            assert prop(pickup,'Available') and prop(pickup,'Collections')==2 and health()==100
            auto=spawn(auto_kind,unreal.Vector(2200,500,96));s['auto']=auto
            assert not prop(auto,'RequireInteraction') and prop(auto,'RespawnDelay')==0
            pawn.set_actor_location(unreal.Vector(2200,500,96),False,True)
            phase('overlap_full');return
        if state=='overlap_full':
            if age<.2:return
            auto=s['auto'];assert unreal.SystemLibrary.is_valid(auto) and prop(auto,'Collections')==0
            set_health(70);phase('inside');return
        if state=='inside':
            if age<.15:return
            assert health()==70 and prop(s['auto'],'Available')
            s['checks'].append('original_overlap_pickup_remains_at_full_health_and_waits_for_new_overlap')
            pawn.set_actor_location(unreal.Vector(2500,500,96),False,True)
            phase('outside');return
        if state=='outside':
            if age<.15:return
            pawn.set_actor_location(unreal.Vector(2200,500,96),False,True)
            phase('auto_used');return
        if state=='auto_used':
            if unreal.SystemLibrary.is_valid(s['auto']):
                assert age<1,'Overlap pickup was not consumed';return
            assert health()==100
            s['checks'].append('native_pawn_overlap_heals_and_destroys_one_shot_pickup')
            target=spawn(pawn.get_class(),unreal.Vector(3500,500,96));s['dead']=target
            probe.call_method('SetHealth',args=(target,0.0))
            fresh=spawn(auto_kind,unreal.Vector(4000,500,96));s['fresh']=fresh
            assert not fresh.call_method('TryCollect',args=(None,))
            assert not fresh.call_method('TryCollect',args=(probe,))
            assert not fresh.call_method('TryCollect',args=(target,))
            set_health(50)
            for value in [0.0,-10.0]:
                probe.call_method('SetHealingAmount',args=(fresh,value))
                assert not fresh.call_method('TryCollect',args=(pawn,)) and health()==50
            assert prop(fresh,'Available') and prop(fresh,'Collections')==0
            s['checks'].append('invalid_targets_dead_pawns_and_nonpositive_healing_do_not_consume')
            pending=spawn(manual_kind,unreal.Vector(4500,500,96))
            probe.call_method('SetRespawnDelay',args=(pending,.25))
            assert pending.call_method('TryCollect',args=(pawn,))
            pending.destroy_actor();s['pending']=pending
            phase('destroyed_timer');return
        if state=='destroyed_timer':
            if age<.5:return
            assert not unreal.SystemLibrary.is_valid(s['pending']) and health()==100
            assert prop(pickup,'Respawns')==2,'Respawn timer repeated without collection'
            s['checks'].append('destroying_pickup_cancels_pending_respawn_without_late_callbacks')
            finish()
    except Exception:finish(traceback.format_exc())
    finally:s['busy']=False

s['handle']=unreal.register_slate_post_tick_callback(tick)
