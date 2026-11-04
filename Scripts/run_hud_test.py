WAIT_EDITOR_COMPILE=False
PREPARE_SCRIPT='Scripts/prepare_hud.py'
TEST_SCRIPT='Tests/verify_hud_pie.py'
RESULT_FILE='Saved/Tests/rogue_hud_pie.json'
from pathlib import Path
exec(compile((Path(__file__).parent/'run_actions_test.py').read_text(encoding='utf-8-sig'),str(Path(__file__).parent/'run_actions_test.py'),'exec'))
