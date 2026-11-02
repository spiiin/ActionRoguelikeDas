"""Shared build-agent entry point: prepare, test real PIE, clean up and quit."""
import json
import time
import traceback
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
TEST_SCRIPT = globals().get('TEST_SCRIPT', 'Tests/verify_actions_pie.py')
RESULT = ROOT / globals().get('RESULT_FILE', 'Saved/Tests/rogue_actions_pie.json')
RESULT.unlink(missing_ok=True)
STATE = {'phase': 'prepare', 'started': time.perf_counter(), 'ticks': 0}


def run_script(relative):
    path = ROOT / relative
    namespace = {'__name__': '__main__', '__file__': str(path)}
    exec(compile(path.read_text(encoding='utf-8-sig'), str(path), 'exec'), namespace)
    return namespace


def fail(error):
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps({'passed': False, 'error': error}, indent=2), encoding='utf-8')
    unreal.log_error('DAS_ROGUE_ACTIONS_RUNNER ' + error)
    STATE['phase'] = 'stop'


def tick(delta):
    if STATE.get('busy'):
        return
    STATE['busy'] = True
    try:
        editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem) or unreal.get_default_object(unreal.LevelEditorSubsystem)
        if STATE['phase'] not in ('stop', 'cleanup') and time.perf_counter() - STATE['started'] > 150:
            raise RuntimeError('Action test runner timed out in ' + STATE['phase'])
        if STATE['phase'] == 'prepare':
            world = editor.get_editor_world()
            if not world or world.get_name() != 'ChestTest':
                return
            unreal.SystemLibrary.execute_console_command(world, 't.IdleWhenNotForeground 0')
            interface = unreal.load_class(None, '/Game/DasRogue/Types/RogueActionHost.RogueActionHost_C')
            assert interface, 'ActionHost interface must exist before typed reference compilation'
            run_script('Scripts/prepare_character.py')
            run_script('Scripts/prepare_action_tests.py')
            level.editor_request_begin_play()
            STATE['phase'] = 'wait_play'
            return
        if STATE['phase'] == 'wait_play':
            world = editor.get_game_world()
            if not world:
                return
            pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
            if not pawn or not pawn.get_editor_property('ControlsBound'):
                return
            STATE['ticks'] += 1
            if STATE['ticks'] < 3:
                return
            for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
                if actor.get_class().get_name() in ('BP_InteractiveChestHinged_C', 'BP_TargetDummy_C'):
                    assert not actor.get_editor_property('LastDasError'), actor.get_editor_property('LastDasError')
            STATE['test'] = run_script(TEST_SCRIPT)
            STATE['phase'] = 'test'
            return
        if STATE['phase'] == 'test':
            if RESULT.exists():
                result = json.loads(RESULT.read_text(encoding='utf-8'))
                unreal.log('DAS_ROGUE_ACTIONS_RUNNER_RESULT ' + json.dumps(result))
                STATE['phase'] = 'stop'
            return
        if STATE['phase'] == 'stop':
            test = STATE.get('test', {}).get('s', {})
            if test.get('handle') and not test.get('done'):
                unreal.unregister_slate_post_tick_callback(test['handle'])
                test['done'] = True
            level.editor_request_end_play()
            STATE['phase'] = 'cleanup'
            return
        if STATE['phase'] == 'cleanup':
            if editor.get_game_world():
                return
            actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            for actor in list(actors.get_all_level_actors()):
                if actor.get_class().get_name() == 'BP_RogueActionProbe_C':
                    actors.destroy_actor(actor)
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
            unreal.unregister_slate_post_tick_callback(STATE['handle'])
            unreal.SystemLibrary.quit_editor()
    except Exception:
        if STATE['phase'] == 'cleanup':
            unreal.log_error(traceback.format_exc())
            unreal.unregister_slate_post_tick_callback(STATE['handle'])
            unreal.SystemLibrary.quit_editor()
        else:
            fail(traceback.format_exc())

    finally:
        STATE['busy'] = False


unreal.load_class(None, '/Game/DasRogue/Types/RogueActionHost.RogueActionHost_C')
STATE['handle'] = unreal.register_slate_post_tick_callback(tick)
unreal.log('DAS_ROGUE_ACTIONS_RUNNER_STARTED')
