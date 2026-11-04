"""Author runtime assets for the DAS director; the game loads .uasset data only."""
from pathlib import Path
import json,runpy,unreal
ROOT=Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT/'Scripts/prepare_director_types.py'))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_name()=='DirectorTest','Open DirectorTest before authoring the director'
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
tools=unreal.AssetToolsHelpers.get_asset_tools()
for name in ['EQS_DirectorSpawn','EQS_DirectorEmpty']:
    path='/Game/DasRogue/Director/'+name
    if not assets.does_asset_exist(path):
        unreal.SystemLibrary.execute_console_command(world,'Das.AI.ImportText /Script/AIModule.EnvQuery '+path+' '+str(ROOT/'Scripts/ai_assets'/(name+'.t3d')))
    assert unreal.load_asset(path),name

def data(name,kind):
    path='/Game/DasRogue/Director/'+name
    result=unreal.load_asset(path)
    if not result:
        factory=unreal.DataAssetFactory();factory.set_editor_property('data_asset_class',kind)
        result=tools.create_asset(name,'/Game/DasRogue/Director',kind,factory)
    assert result,name
    result.modify(True)
    return result

monster_kind=unreal.load_class(None,'/Game/DasRogue/Types/BP_RogueMonsterData.BP_RogueMonsterData_C')
monster=data('DA_DirectorMinion',monster_kind)
monster.set_editor_property('MonsterClass',unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueBehaviorMinion.BP_RogueBehaviorMinion_C'))
monster.set_editor_property('Actions',[unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionDropLoot.BP_RogueActionDropLoot_C')])
monster.set_editor_property('LootCoins',50)
monster.set_editor_property('HealthWidgetClass',unreal.load_class(None,'/Game/DasRogue/UI/WBP_RogueHealth.WBP_RogueHealth_C'))

row_struct=unreal.load_object(None,'/Game/DasRogue/Types/RogueMonsterSpawnData.RogueMonsterSpawnData')
assert row_struct
table=unreal.load_asset('/Game/DasRogue/Director/DT_DirectorMonsters')
if not table:
    factory=unreal.DataTableFactory();factory.set_editor_property('struct',row_struct)
    table=tools.create_asset('DT_DirectorMonsters','/Game/DasRogue/Director',unreal.DataTable,factory)
table.modify(True)
rows=[dict(Name='Grunt',MonsterData=monster.get_path_name(),SpawnCost=5,SpawnWeight=3),
      dict(Name='Heavy',MonsterData=monster.get_path_name(),SpawnCost=9,SpawnWeight=1),
      dict(Name='Disabled',MonsterData=monster.get_path_name(),SpawnCost=0,SpawnWeight=0)]
assert unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(table,json.dumps(rows))

factory=unreal.CSVImportFactory()
settings=unreal.CSVImportSettings()
settings.set_editor_property('import_type',unreal.CSVImportType.ECSV_CURVE_FLOAT)
settings.set_editor_property('import_curve_interp_mode',unreal.RichCurveInterpMode.RCIM_LINEAR)
factory.set_editor_property('automated_import_settings',settings)
task=unreal.AssetImportTask()
task.set_editor_property('filename',str(ROOT/'Scripts/director_assets/C_DirectorIncome.csv'))
task.set_editor_property('destination_path','/Game/DasRogue/Director')
task.set_editor_property('automated',True)
task.set_editor_property('replace_existing',True)
task.set_editor_property('factory',factory)
tools.import_asset_tasks([task])
curve=unreal.load_asset('/Game/DasRogue/Director/C_DirectorIncome')
assert curve
assert abs(curve.get_float_value(30)-12)<.01

config_kind=unreal.load_class(None,'/Game/DasRogue/Director/BP_RogueDirectorConfig.BP_RogueDirectorConfig_C')
config=data('DA_Director',config_kind)
config.set_editor_property('DisplayName','Ranged minions')
config.set_editor_property('MonsterSpawnTable',table)
config.set_editor_property('SpawnLocationQuery',unreal.load_asset('/Game/DasRogue/Director/EQS_DirectorSpawn'))
config.set_editor_property('CreditGainCurve',curve)
config.set_editor_property('StartingCredits',15.0)
config.set_editor_property('TickInterval',.5)
config.set_editor_property('TimeBetweenWaves',2.0)

actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in list(actors.get_all_level_actors()):
    if actor.get_class().get_name().startswith('BP_'):actors.destroy_actor(actor)
    elif isinstance(actor,unreal.PlayerStart):actor.set_actor_location(unreal.Vector(3200,-1200,96),False,True)
kind=unreal.load_class(None,'/Game/DasRogue/Director/BP_RogueSpawnDirector.BP_RogueSpawnDirector_C')
director=actors.spawn_actor_from_class(kind,unreal.Vector(3800,600,96));assert director
director.set_actor_label('daScript spawn director - seeded waves')
director.set_editor_property('Configurations',[config])
director.set_editor_property('BotLimit',5)
unreal.SystemLibrary.execute_console_command(world,'RebuildNavigation')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
runpy.run_path(str(ROOT/'Scripts/prepare_action_tests.py'))
print('DAS_DIRECTOR_PREPARE PASS')
