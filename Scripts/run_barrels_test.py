from pathlib import Path
PREPARE_SCRIPT='Scripts/prepare_barrels.py'
AI_TEST=True
TEST_SCRIPT='Tests/verify_barrels_pie.py'
RESULT_FILE='Saved/Tests/rogue_barrels_pie.json'
exec(compile((Path(__file__).parent/'run_actions_test.py').read_text(encoding='utf-8-sig'),
             str(Path(__file__).parent/'run_actions_test.py'),'exec'))
