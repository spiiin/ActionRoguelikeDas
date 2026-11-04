WAIT_EDITOR_COMPILE=False  # Native PIE preflight prepares the configured roots in unattended tests.
from pathlib import Path
PREPARE_SCRIPT='Scripts/prepare_coins_test.py'
WAIT_NAVIGATION=True
AI_TEST=True
TEST_SCRIPT='Tests/verify_coins_pie.py'
RESULT_FILE='Saved/Tests/rogue_coins_pie.json'
exec(compile((Path(__file__).parent/'run_actions_test.py').read_text(encoding='utf-8-sig'),
             str(Path(__file__).parent/'run_actions_test.py'),'exec'))
