from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('run_actions_test.py')),init_globals={
    'TEST_SCRIPT':'Tests/verify_point_impact_pie.py',
    'RESULT_FILE':'Saved/Tests/rogue_point_impact_pie.json',
    'OVERWHELM_TEST':True,
    'POINT_IMPACT_TEST':True,
})
