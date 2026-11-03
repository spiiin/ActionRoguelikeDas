"""Import batched coin/loot assets. All runtime policy remains in daScript."""
import unreal
from pathlib import Path
__import__('runpy').run_path(str(Path(__file__).resolve().with_name('prepare_attribute_sets.py')))

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for source,path,identity in [
    ('rogue_monster_data','/Game/DasRogue/Types/BP_RogueMonsterData','rogue.RogueMonsterData'),
    ('rogue_coin_pickup_subsystem','/Game/DasRogue/Pickups/BP_RogueCoinPickupSubsystem','rogue.RogueCoinPickupSubsystem'),
    ('rogue_action_drop_loot','/Game/DasRogue/Actions/BP_RogueActionDropLoot','rogue.RogueActionDropLoot'),
    ('rogue_coin_test_actor','/Game/DasRogue/Pickups/BP_RogueCoinTestActor','roguedemo.RogueCoinTestActor'),
]:
    unreal.SystemLibrary.execute_console_command(world,f'Das.DSL.Apply {source}.das {path} {identity}')
    name=path.rsplit('/',1)[-1]
    assert unreal.load_class(None,path+'.'+name+'_C'),identity+' import failed'

system_kind=unreal.load_class(None,'/Game/DasRogue/Pickups/BP_RogueCoinPickupSubsystem.BP_RogueCoinPickupSubsystem_C')
for path in ['/Game/DasRogue/Actions/BP_RogueActionDropLoot','/Game/DasRogue/Pickups/BP_RogueCoinTestActor']:
    asset=unreal.load_asset(path);asset.modify(True)
    unreal.get_default_object(asset.generated_class()).set_editor_property('CoinSystemClass',system_kind)

data_kind=unreal.load_class(None,'/Game/DasRogue/Types/BP_RogueMonsterData.BP_RogueMonsterData_C')
data=unreal.load_asset('/Game/DasRogue/AI/DA_LootRegression')
if not data:
    factory=unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class',data_kind)
    data=unreal.AssetToolsHelpers.get_asset_tools().create_asset('DA_LootRegression','/Game/DasRogue/AI',data_kind,factory)
assert data
data.modify(True)
data.set_editor_property('LootCoins',37)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
print('DAS_COINS_PREPARE PASS')
