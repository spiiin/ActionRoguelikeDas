from pathlib import Path
import unreal
# Create the first map before the shared runner retains any world references.
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem) or unreal.get_default_object(unreal.LevelEditorSubsystem)
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
path='/Game/DasRogue/Maps/EnvironmentTest'
if not assets.does_asset_exist(path):
    assert level.new_level_from_template(path,'/Game/DasRogue/Maps/ChestTest')
else:
    assert level.load_level(path)
WAIT_EDITOR_COMPILE=False
PREPARATION_MAPS=('EnvironmentTest',)
PREPARE_SCRIPT='Scripts/prepare_environment.py'
TEST_SCRIPT='Tests/verify_environment_pie.py'
RESULT_FILE='Saved/Tests/rogue_environment_pie.json'
TEST_TIMEOUT=45
exec(compile((Path(__file__).parent/'run_actions_test.py').read_text(encoding='utf-8-sig'),str(Path(__file__).parent/'run_actions_test.py'),'exec'))
