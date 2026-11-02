"""Set up local resources and verify them in real PIE through the shared runner."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('run_actions_test.py')),init_globals={
    'TEST_SCRIPT':'Tests/verify_presentation_pie.py',
    'RESULT_FILE':'Saved/Tests/rogue_presentation_pie.json',
    'EXTERNAL_PRESENTATION':True,
})
