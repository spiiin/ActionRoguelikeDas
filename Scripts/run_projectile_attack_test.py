"""Run the projectile ability checks through the shared normal-editor harness."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('run_actions_test.py')), init_globals={
    'TEST_SCRIPT': 'Tests/verify_projectile_attack_pie.py',
    'RESULT_FILE': 'Saved/Tests/rogue_projectile_attack_pie.json',
})
