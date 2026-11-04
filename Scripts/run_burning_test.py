from pathlib import Path
PREPARE_SCRIPT='Scripts/prepare_burning.py'
TEST_SCRIPT='Tests/verify_burning_pie.py'
RESULT_FILE='Saved/Tests/rogue_burning_pie.json'
exec(compile((Path(__file__).parent/'run_actions_test.py').read_text(encoding='utf-8-sig'),
             str(Path(__file__).parent/'run_actions_test.py'),'exec'))
