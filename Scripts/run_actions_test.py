"""Shared build-agent entry point: prepare, test real PIE, clean up and quit."""
import json
import time
import traceback
import re
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
        if STATE['phase'] not in ('stop', 'cleanup') and time.perf_counter() - STATE['started'] > (600 if globals().get('EXTERNAL_PRESENTATION') else 150):
            raise RuntimeError('Action test runner timed out in ' + STATE['phase'])
        if STATE['phase'] == 'prepare':
            world = editor.get_editor_world()
            if not world or world.get_name() != 'ChestTest':
                return
            unreal.SystemLibrary.execute_console_command(world, 't.IdleWhenNotForeground 0')
            interface = unreal.load_class(None, '/Game/DasRogue/Types/RogueActionHost.RogueActionHost_C')
            assert interface, 'ActionHost interface must exist before typed reference compilation'
            if globals().get('EXTERNAL_PRESENTATION'):
                run_script('Scripts/prepare_external_assets.py')
            run_script('Scripts/prepare_character.py')
            if globals().get('OVERWHELM_TEST'):
                run_script('Scripts/prepare_overwhelm.py')
            run_script('Scripts/prepare_action_tests.py')
            if globals().get('ACTION_EFFECTS'):
                run_script('Scripts/prepare_effect_tests.py')
            if globals().get('EXTERNAL_PRESENTATION'):
                run_script('Scripts/prepare_presentation_tests.py')
            STATE['phase'] = 'wait_startup'
            STATE['warm_ticks'] = 0
            return
        if STATE['phase'] == 'wait_startup':
            # Map-open startup work runs on a core ticker after the Python setup
            # callback. Starting PIE earlier can run that work during gameplay.
            command=unreal.SystemLibrary.get_command_line()
            match=re.search(r'-abslog=(?:"([^"]+)"|([^ ]+))',command,re.IGNORECASE)
            assert match,'Harness requires an explicit log path'
            logfile=Path(match.group(1) or match.group(2))
            log=logfile.read_text(encoding='utf-8',errors='replace') if logfile.exists() else ''
            if not re.search(r'DAS_EDITOR_COMPILE_ALL scripts=\d+ failed=0',log):
                return
            STATE['warm_ticks']+=1
            if STATE['warm_ticks']<4:return
            level.editor_request_begin_play()
            STATE['phase']='wait_play'
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
