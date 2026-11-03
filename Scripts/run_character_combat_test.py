"""Camera aiming, cover and death through the shared PIE harness."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('run_actions_test.py')),init_globals={
    'PREPARE_SCRIPT':'Scripts/prepare_character_combat_test.py',
    'TEST_SCRIPT':'Tests/verify_character_combat_pie.py',
    'RESULT_FILE':'Saved/Tests/rogue_character_combat_pie.json',
})
