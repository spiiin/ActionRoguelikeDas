from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
globals().update(AI_TEST=True,AI_PRESENTATION=True,TEST_SCRIPT='Tests/verify_ai_presentation_pie.py',RESULT_FILE='Saved/Tests/rogue_ai_presentation_pie.json')
exec(compile((ROOT/'Scripts/run_actions_test.py').read_text(encoding='utf-8'),str(ROOT/'Scripts/run_actions_test.py'),'exec'),globals())
