"""Input lifetime checks through the normal editor/PIE harness."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('run_actions_test.py')), init_globals={
    'TEST_SCRIPT': 'Tests/verify_input_pie.py',
    'RESULT_FILE': 'Saved/Tests/rogue_input_pie.json',
})
