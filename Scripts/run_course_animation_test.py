from pathlib import Path
PREPARE_SCRIPT='Scripts/prepare_course_animation.py'
EXTERNAL_PRESENTATION=True
TEST_SCRIPT='Tests/verify_course_animation_pie.py'
RESULT_FILE='Saved/Tests/rogue_course_animation_pie.json'
exec(compile((Path(__file__).parent/'run_actions_test.py').read_text(encoding='utf-8-sig'),
             str(Path(__file__).parent/'run_actions_test.py'),'exec'))
