from pathlib import Path
PICKUP_TEST=True
PREPARE_SCRIPT='Scripts/prepare_pickup_test.py'
TEST_SCRIPT='Tests/verify_pickup_pie.py'
RESULT_FILE='Saved/Tests/rogue_pickup_pie.json'
exec(compile((Path(__file__).parent/'run_actions_test.py').read_text(encoding='utf-8-sig'),
             str(Path(__file__).parent/'run_actions_test.py'),'exec'))
