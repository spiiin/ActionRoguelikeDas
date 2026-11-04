from pathlib import Path
PREPARE_SCRIPT='Scripts/prepare_additional_attacks_test.py'
TEST_SCRIPT='Tests/verify_additional_attacks_pie.py'
RESULT_FILE='Saved/Tests/rogue_additional_attacks_pie.json'
PREPARATION_TIMEOUT=600
exec(compile((Path(__file__).parent/'run_actions_test.py').read_text(encoding='utf-8-sig'),
             str(Path(__file__).parent/'run_actions_test.py'),'exec'))
