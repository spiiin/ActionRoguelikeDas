TEST_TIMEOUT=150
WAIT_EDITOR_COMPILE=False  # Unattended editor: native PIE preflight compiles the configured gameplay roots.
from pathlib import Path
PREPARE_SCRIPT='Scripts/prepare_behavior_tree.py'
TEST_SCRIPT='Tests/verify_behavior_tree_pie.py'
RESULT_FILE='Saved/Tests/rogue_behavior_tree_pie.json'
WAIT_NAVIGATION=True
AI_TEST=True
exec(compile((Path(__file__).parent/'run_actions_test.py').read_text(encoding='utf-8-sig'),str(Path(__file__).parent/'run_actions_test.py'),'exec'))
