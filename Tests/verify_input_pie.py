"""Native setup/restart/unpossess input lifetime in a real PIE world."""
from pathlib import Path
import json
import time
import traceback
import unreal

root = Path(__file__).resolve().parents[1]
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
player = unreal.GameplayStatics.get_player_controller(world, 0)
original = unreal.GameplayStatics.get_player_pawn(world, 0)
probe = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
             if a.get_class().get_name() == 'BP_RogueActionProbe_C')
subsystems = [v for v in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem)
              if v.get_outer().get_class().get_name() == 'LocalPlayer']
inputs = max(subsystems, key=lambda v: int(v.get_outer().get_name().rsplit('_', 1)[-1]))
interact = unreal.load_asset('/Game/DasRogue/Input/IA_Interact')
move = unreal.load_asset('/Game/DasRogue/Input/IA_Move')
fire = unreal.load_asset('/Game/DasRogue/Input/IA_Fire')
sprint = unreal.load_asset('/Game/DasRogue/Input/IA_Sprint')

def prop(obj, name): return obj.get_editor_property(name)
def now(): return unreal.GameplayStatics.get_time_seconds(world)
def inject(action): inputs.inject_input_vector_for_action(action, unreal.Vector(1, 0, 0), [], [])
def count(): return prop(player, 'InteractPresses')
def primary(pawn):
    tag = unreal.GameplayTag()
    assert tag.import_text('Action.PrimaryAttack')
    return prop(pawn, 'ActionSystem').call_method('FindAction', args=(tag,))

assert prop(player, 'ControlsBound') and prop(original, 'ControlsBound')
assert prop(player, 'InputSetups') == 1 and prop(original, 'InputSetups') == 1
s = {'phase': 'initial', 'at': now(), 'started': time.perf_counter(), 'checks': [], 'done': False,
     'presses': count(), 'new_pawn': None}

def phase(value): s['phase'] = value; s['at'] = now()
def finish(error=None):
    s['done'] = True
    unreal.unregister_slate_post_tick_callback(s['handle'])
    result = root/'Saved/Tests/rogue_input_pie.json'
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text(json.dumps({'passed': error is None, 'error': error, 'checks': s['checks']}, indent=2))

def tick(delta):
    if s['done']: return
    try:
        assert time.perf_counter()-s['started'] < 45, s['phase']
        assert not prop(player, 'LastDasError'), prop(player, 'LastDasError')
        for pawn in [original, s['new_pawn']]:
            if pawn: assert not prop(pawn, 'LastDasError'), prop(pawn, 'LastDasError')
        age = now()-s['at']
        if s['phase'] == 'initial':
            if age < .25: return
            assert prop(player, 'InputSetups') == 1 and prop(original, 'InputSetups') == 1
            s['checks'].append('native_setup_once_after_begin_play_without_polling')
            inject(interact); phase('interact'); return
        if s['phase'] == 'interact':
            if age < .15: return
            assert count() == s['presses']+1, 'Initial interaction binding missing or duplicated'
            inject(sprint); phase('held'); return
        if s['phase'] == 'held':
            inject(sprint)
            if age < .1: return
            movement = prop(original, 'character_movement')
            assert abs(prop(movement, 'max_walk_speed')-720) < .1
            player.call_method('UnPossess', args=())
            assert not prop(original, 'ControlsBound'), 'UnPossessed did not remove character input'
            assert abs(prop(movement, 'max_walk_speed')-450) < .1, 'Held sprint survived unpossess'
            player.possess(original)
            phase('repossess'); return
        if s['phase'] == 'repossess':
            if prop(original, 'InputSetups') < 2:
                assert age < 2, 'PawnClientRestart did not deliver input setup'; return
            assert prop(original, 'InputSetups') == 2 and prop(original, 'ControlsBound')
            assert prop(player, 'InputSetups') == 1
            s['moves'] = prop(original, 'MoveEvents')
            inject(move); phase('movement'); return
        if s['phase'] == 'movement':
            if age < .15: return
            assert prop(original, 'MoveEvents') > s['moves']
            s['checks'].append('same_pawn_repossess_rebuilds_native_input')
            pawn = probe.call_method('Spawn', args=(original.get_class(), unreal.Vector(800, -600, 100), unreal.Rotator()))
            assert pawn and not prop(pawn, 'ControlsBound') and prop(pawn, 'InputSetups') == 0
            s['new_pawn'] = pawn
            player.possess(pawn)
            phase('new_pawn'); return
        if s['phase'] == 'new_pawn':
            pawn = s['new_pawn']
            if prop(pawn, 'InputSetups') < 1:
                assert age < 2, 'New pawn input was not set up'; return
            assert prop(pawn, 'InputSetups') == 1 and prop(pawn, 'ControlsBound')
            assert not prop(original, 'ControlsBound')
            s['moves'] = prop(pawn, 'MoveEvents')
            s['old_moves'] = prop(original, 'MoveEvents')
            s['presses'] = count()
            s['starts'] = prop(primary(pawn), 'Starts')
            inject(move); inject(interact); inject(fire)
            phase('new_input'); return
        if s['phase'] == 'new_input':
            if age < .4: return
            pawn = s['new_pawn']
            assert prop(pawn, 'MoveEvents') > s['moves']
            assert prop(original, 'MoveEvents') == s['old_moves'], 'Input still reaches the unpossessed pawn'
            assert count() == s['presses']+1, 'Controller interaction binding duplicated on possession'
            assert prop(primary(pawn), 'Starts') == s['starts']+1, 'Fire binding missing or duplicated'
            s['checks'].append('new_pawn_owns_movement_and_controller_input_is_not_duplicated')
            player.possess(original)
            phase('return'); return
        if s['phase'] == 'return':
            if prop(original, 'InputSetups') < 3:
                assert age < 2, 'Returning to the first pawn lost input'; return
            assert prop(original, 'ControlsBound') and not prop(s['new_pawn'], 'ControlsBound')
            assert prop(player, 'InputSetups') == 1
            s['checks'].append('return_to_previous_pawn_restores_input')
            finish()
    except Exception:
        finish(traceback.format_exc())

s['handle'] = unreal.register_slate_post_tick_callback(tick)
