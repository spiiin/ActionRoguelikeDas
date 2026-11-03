from pathlib import Path
PREPARE_SCRIPT='Scripts/prepare_patrol_test.py'
WAIT_NAVIGATION=True
TEST_SCRIPT='Tests/verify_patrol_pie.py'
RESULT_FILE='Saved/Tests/rogue_patrol_pie.json'
AI_TEST=True
exec(compile((Path(__file__).parent/'run_actions_test.py').read_text(encoding='utf-8-sig'),
             str(Path(__file__).parent/'run_actions_test.py'),'exec'))
