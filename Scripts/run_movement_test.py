"""Native movement parity through the normal PIE harness."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('run_actions_test.py')),init_globals={
    'TEST_SCRIPT':'Tests/verify_movement_pie.py',
    'RESULT_FILE':'Saved/Tests/rogue_movement_pie.json',
})
