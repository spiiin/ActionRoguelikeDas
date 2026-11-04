"""Public data profile; no licensed meshes or course native classes are required."""
from pathlib import Path
import runpy,unreal
ROOT=Path(__file__).resolve().parents[1]
# Core game assets are versioned; only this stage's changed dependency needs reimport.
setup_world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(setup_world,'Das.DSL.Reimport /Game/DasRogue/Actions/BP_RogueActionProjectileAttack')
runpy.run_path(str(ROOT/'Scripts/prepare_action_tests.py'))
runpy.run_path(str(ROOT/'Scripts/prepare_coins.py'))
runpy.run_path(str(ROOT/'Scripts/prepare_ai.py'))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for source,name,folder,module in [('rogue_monster_spawner','RogueMonsterSpawner','AI','rogue'),('rogue_monster_probe','RogueMonsterProbe','Tests','roguetest')]:
    path='/Game/DasRogue/'+folder+'/BP_'+name
    unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply '+source+'.das '+path+' '+module+'.'+name)
    assert unreal.load_class(None,path+'.BP_'+name+'_C')
kind=unreal.load_class(None,'/Game/DasRogue/Types/BP_RogueMonsterData.BP_RogueMonsterData_C')
path='/Game/DasRogue/AI/DA_RangedMinion'
data=unreal.load_asset(path)
if not data:
    factory=unreal.DataAssetFactory();factory.set_editor_property('data_asset_class',kind)
    data=unreal.AssetToolsHelpers.get_asset_tools().create_asset('DA_RangedMinion','/Game/DasRogue/AI',kind,factory)
assert data
data.modify(True)
data.set_editor_property('MonsterClass',unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueAICharacter.BP_RogueAICharacter_C'))
data.set_editor_property('Actions',[unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionDropLoot.BP_RogueActionDropLoot_C')])
data.set_editor_property('LootCoins',100)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
print('DAS_MONSTER_DATA_PREPARE PASS')
