WAIT_EDITOR_COMPILE=False  # Unattended editor: native PIE preflight compiles the configured gameplay roots.
from pathlib import Path
PREPARE_SCRIPT='Scripts/prepare_monster_data.py'
TEST_SCRIPT='Tests/verify_monster_data_pie.py'
RESULT_FILE='Saved/Tests/rogue_monster_data_pie.json'
exec(compile((Path(__file__).parent/'run_actions_test.py').read_text(encoding='utf-8-sig'),str(Path(__file__).parent/'run_actions_test.py'),'exec'))
