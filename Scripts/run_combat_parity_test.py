import unreal
unreal.log("DAS_COMBAT_MODULE_CACHE="+str(unreal.SystemLibrary.get_console_variable_int_value("das.EditorModuleCache")))
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
globals().update(AI_TEST=True,AI_PRESENTATION=True,EXTERNAL_PRESENTATION=True,
    TEST_SCRIPT='Tests/verify_combat_parity_pie.py',RESULT_FILE='Saved/Tests/rogue_combat_parity_pie.json')
exec(compile((ROOT/'Scripts/run_actions_test.py').read_text(encoding='utf-8'),str(ROOT/'Scripts/run_actions_test.py'),'exec'),globals())
