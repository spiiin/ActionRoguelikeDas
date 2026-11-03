"""Run AttributeSet and native damage/Rage regression checks in PIE."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('run_actions_test.py')),init_globals={
    'ATTRIBUTE_TEST':True,
    'TEST_SCRIPT':'Tests/verify_attributes_pie.py',
    'RESULT_FILE':'Saved/Tests/rogue_attributes_pie.json',
})
