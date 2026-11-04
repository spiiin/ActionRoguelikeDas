WAIT_EDITOR_COMPILE=False
WAIT_NAVIGATION=True
AI_TEST=True
PREPARATION_MAPS=('DirectorTest',)
PREPARE_SCRIPT='Scripts/prepare_director.py'
TEST_SCRIPT='Tests/verify_director_pie.py'
RESULT_FILE='Saved/Tests/rogue_director_pie.json'
TEST_TIMEOUT=90
from pathlib import Path
exec(compile((Path(__file__).parent/'run_actions_test.py').read_text(encoding='utf-8-sig'),str(Path(__file__).parent/'run_actions_test.py'),'exec'))
