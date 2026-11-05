from pathlib import Path
import unreal
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem) or unreal.get_default_object(unreal.LevelEditorSubsystem)
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
path='/Game/DasRogueExternal/Maps/P_OpenWorldTestMap_Das'
if not assets.does_asset_exist(path):
    assert level.new_level_from_template(path,'/Engine/Maps/Templates/Template_Default')
else:
    assert level.load_level(path)
WAIT_EDITOR_COMPILE=False
AI_TEST=True
WAIT_NAVIGATION=True
NAVIGATION_MAPS=("P_OpenWorldTestMap_Das",)
NAVIGATION_FROM=(-520,1180,100)
NAVIGATION_TO=(-650,540,100)
NAVIGATION_MIN_LENGTH=600
NAVIGATION_TIMEOUT=120
PREPARATION_MAPS=('P_OpenWorldTestMap_Das',)
PREPARATION_TIMEOUT=900
PREPARE_SCRIPT='Scripts/prepare_course_world.py'
TEST_SCRIPT='Tests/verify_course_world_pie.py'
RESULT_FILE='Saved/Tests/rogue_course_world_pie.json'
TEST_TIMEOUT=90
exec(compile((Path(__file__).parent/'run_actions_test.py').read_text(encoding='utf-8-sig'),str(Path(__file__).parent/'run_actions_test.py'),'exec'))
