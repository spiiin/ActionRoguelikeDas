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
        # Compile/import preparation must not consume the gameplay test budget.
        if STATE['phase'] == 'test':
            if time.perf_counter()-STATE['test_started'] > globals().get('TEST_TIMEOUT',75):
                detail=STATE.get('test',{}).get('s',{}).get('phase','unknown')
                raise RuntimeError('Gameplay test timed out in '+str(detail))
        elif STATE['phase'] not in ('stop','cleanup'):
            preparation_limit=globals().get('PREPARATION_TIMEOUT', 600)
            if time.perf_counter()-STATE['started'] > preparation_limit:
                raise RuntimeError('Preparation timed out in '+STATE['phase'])
        if STATE['phase'] == 'prepare':
            world = editor.get_editor_world()
            allowed_maps = globals().get('PREPARATION_MAPS', ('ChestTest','PatrolTest','BehaviorTest') if globals().get('WAIT_NAVIGATION') else ('ChestTest',))
            if not world or world.get_name() not in allowed_maps:
                return
            unreal.SystemLibrary.execute_console_command(world, 't.IdleWhenNotForeground 0')
            interface = unreal.load_class(None, '/Game/DasRogue/Types/RogueActionHost.RogueActionHost_C')
            assert interface, 'ActionHost interface must exist before typed reference compilation'
            if globals().get('PREPARE_SCRIPT'):
                run_script(PREPARE_SCRIPT)
            else:
                if globals().get('EXTERNAL_PRESENTATION'):
                    run_script('Scripts/prepare_external_assets.py')
                run_script('Scripts/prepare_character.py')
                if globals().get('OVERWHELM_TEST'):
                    run_script('Scripts/prepare_overwhelm.py')
                run_script('Scripts/prepare_action_tests.py')
                if globals().get('ATTRIBUTE_TEST'):
                    run_script('Scripts/prepare_attribute_test.py')
                if globals().get('POINT_IMPACT_TEST'):
                    run_script('Scripts/prepare_point_impact.py')
                if globals().get('ACTION_EFFECTS'):
                    run_script('Scripts/prepare_effect_tests.py')
                if globals().get('EXTERNAL_PRESENTATION'):
                    run_script('Scripts/prepare_presentation_tests.py')
                if globals().get('AI_TEST'):
                    run_script('Scripts/prepare_ai.py')
                if globals().get('AI_PRESENTATION'):
                    run_script('Scripts/prepare_ai_presentation.py')
            STATE['phase'] = 'wait_startup'
            STATE['warm_ticks'] = 0
            return
        if STATE['phase'] == 'wait_navigation':
            world=editor.get_editor_world()
            assert world and world.get_name() in ('PatrolTest','BehaviorTest','DirectorTest')
            STATE.setdefault('nav_started',time.perf_counter())
            nav_age=time.perf_counter()-STATE['nav_started']
            if nav_age>1.0 and not STATE.get('nav_rebuild_requested'):
                # Allow the new Recast actor to register before requesting the build.
                unreal.SystemLibrary.execute_console_command(world,'RebuildNavigation')
                STATE['nav_rebuild_requested']=True
            assert nav_age<60,'Recast navigation did not produce a complete editor path'
            path=unreal.NavigationSystemV1.find_path_to_location_synchronously(world,unreal.Vector(3200,0,10),unreal.Vector(4400,0,10))
            if not path or not path.is_valid() or path.is_partial():
                return
            assert path.get_path_length()>1250,'NavMesh path did not detour around obstacle'
            level.save_current_level()
            STATE['navigation_ready']=True
            STATE['phase']='wait_startup'
            return
        if STATE['phase'] == 'wait_startup':
            # Map-open startup work runs on a core ticker after the Python setup
            # callback. Starting PIE earlier can run that work during gameplay.
            command=unreal.SystemLibrary.get_command_line()
            match=re.search(r'-abslog=(?:"([^"]+)"|([^ ]+))',command,re.IGNORECASE)
            assert match,'Harness requires an explicit log path'
            logfile=Path(match.group(1) or match.group(2))
            log=logfile.read_text(encoding='utf-8',errors='replace') if logfile.exists() else ''
            startup_results = re.findall(r'DAS_EDITOR_COMPILE_ALL scripts=\d+ failed=(\d+)',log)
            if startup_results and int(startup_results[-1]):
                raise RuntimeError('Startup compilation failed; inspect DAS_EDITOR_COMPILE_ALL and BlueprintLog')
            if globals().get('WAIT_EDITOR_COMPILE',True) and not re.search(r'DAS_EDITOR_COMPILE_ALL scripts=\d+ failed=0',log):
                return
            STATE['warm_ticks']+=1
            if STATE['warm_ticks']<4:return
            if globals().get('WAIT_NAVIGATION') and not STATE.get('navigation_ready'):
                STATE['phase']='wait_navigation'
                return
            level.editor_request_begin_play()
            STATE['play_requested'] = time.perf_counter()
            STATE['phase']='wait_play'
            return
        if STATE['phase'] == 'wait_play':
            world = editor.get_game_world()
            if not world:
                return
            pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
            # PIE can expose its temporary spectator before the gameplay pawn is possessed.
            if not pawn or not isinstance(pawn, unreal.Character):
                if time.perf_counter() - STATE['play_requested'] > 10.0:
                    mode = unreal.GameplayStatics.get_game_mode(world)
                    kind = mode.get_editor_property('default_pawn_class') if mode else None
                    raise RuntimeError(f'Gameplay pawn did not become ready: pawn={pawn}, default_pawn_class={kind}')
                return
            if not pawn.get_editor_property('ControlsBound'):
                if time.perf_counter()-STATE['play_requested'] > 10:
                    controller=unreal.GameplayStatics.get_player_controller(world,0)
                    raise RuntimeError('Native input setup did not complete: pawn='+str(pawn.get_editor_property('LastDasError'))+
                        ', controller='+str(controller.get_editor_property('LastDasError') if controller else None))
                return
            STATE['ticks'] += 1
            if STATE['ticks'] < 3:
                return
            for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
                if actor.get_class().get_name() in ('BP_InteractiveChestHinged_C', 'BP_TargetDummy_C'):
                    assert not actor.get_editor_property('LastDasError'), actor.get_editor_property('LastDasError')
            if not globals().get('AI_TEST'):
                for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Character):
                    if actor.get_class().get_name()=='BP_RogueAICharacter_C':
                        controller=actor.get_controller()
                        if controller:controller.destroy_actor()
                        actor.destroy_actor()
            STATE['test_started'] = time.perf_counter()
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
            teardown = STATE.get('test', {}).get('verify_teardown')
            if teardown:
                try:
                    teardown()
                except Exception:
                    RESULT.write_text(json.dumps({'passed':False,'error':traceback.format_exc()},indent=2),encoding='utf-8')
                    unreal.log_error('DAS_ROGUE_TEARDOWN '+traceback.format_exc())
            actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            for actor in list(actors.get_all_level_actors()):
                if actor.get_class().get_name() in ('BP_RogueActionProbe_C','BP_RogueAttributeProbe_C'):
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
