"""Rebuild the original course layout locally; replace game actors with DAS classes."""
from pathlib import Path
import unreal,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/'Saved/ExternalAssets/course_world'
LAYOUT=json.loads((LOCAL/'layout.json').read_text())
COINS=json.loads((ROOT/'ExternalAssets.json').read_text())['course_coins']
TARGET='/Game/DasRogueExternal/Maps/P_OpenWorldTestMap_Das'
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_name()=='P_OpenWorldTestMap_Das'
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
# Import native merged heightmaps, preserving the original sculpted terrain.
# Source edit-layer history remains in the original export, not in this runtime scene.
if assets.get_metadata_tag(world,'DasCourseGeometry')!='6':
    for actor in list(actors.get_all_level_actors()):actors.destroy_actor(actor)
    unreal.SystemLibrary.execute_console_command(world,'Das.World.ImportText '+str(LOCAL/'native_geometry.t3d').replace('\\','/'))
    assert assets.get_metadata_tag(world,'DasWorldImportComplete')=='1', 'Native geometry import did not finish'
    scene=list(actors.get_all_level_actors())
    proxies=[a for a in scene if a.get_class().get_path_name()=='/Script/Landscape.LandscapeStreamingProxy']
    assert len(proxies)==64,('Expected all 64 source landscape proxies',len(proxies))
    assert len([a for a in scene if isinstance(a,unreal.StaticMeshActor)])==9
    assets.set_metadata_tag(world,'DasCourseGeometry','6')
# Validate editor placements before physics can settle movable source props.
by_label={a.get_actor_label():a for a in actors.get_all_level_actors()}
for source in LAYOUT['actors']:
    actor=by_label.get(source['label'])
    if actor:
        assert (actor.get_actor_location()-unreal.Vector(*source['pose']['location'])).length()<.1,source['label']
# Authored gameplay is stored separately from the acquired geometry.
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Reimport /Game/DasRogue/BP_RogueItemChest')
for source,name in [('rogue_course_chest','RogueCourseChest'),('rogue_course_stun_zone','RogueCourseStunZone'),('rogue_course_world','RogueCourseWorld')]:
    path='/Game/DasRogue/World/BP_'+name
    command='Das.DSL.Reimport '+path if assets.does_asset_exist(path) else 'Das.DSL.Apply '+source+'.das '+path+' roguedemo.'+name
    unreal.SystemLibrary.execute_console_command(world,command)
    assert unreal.load_class(None,path+'.BP_'+name+'_C'),name
# Use the original spawn query and preserve both income curves without resampling.
path='/Game/DasRogue/AI/BT/BP_RogueEQSAlivePlayers'
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Reimport '+path if assets.does_asset_exist(path) else 'Das.DSL.Apply rogue_eqs_alive_players.das '+path+' rogue.RogueEQSAlivePlayers')
assert unreal.load_class(None,path+'.BP_RogueEQSAlivePlayers_C')
query_path='/Game/DasRogueExternal/Director/EQS_FindMonsterSpawn'
if not assets.does_asset_exist(query_path):
    unreal.SystemLibrary.execute_console_command(world,'Das.AI.ImportText /Script/AIModule.EnvQuery '+query_path+' '+str(LOCAL/'spawn_query.t3d'))
query=unreal.load_asset(query_path);assert query
tools=unreal.AssetToolsHelpers.get_asset_tools()
def data_asset(name,kind):
    path='/Game/DasRogueExternal/Director/'+name
    obj=unreal.load_asset(path)
    if not obj:
        factory=unreal.DataAssetFactory();factory.set_editor_property('data_asset_class',kind)
        obj=tools.create_asset(name,'/Game/DasRogueExternal/Director',kind,factory)
    assert obj,name
    obj.modify(True);return obj
monster=data_asset('DA_CourseMinion',unreal.load_class(None,'/Game/DasRogue/Types/BP_RogueMonsterData.BP_RogueMonsterData_C'))
monster.set_editor_property('MonsterClass',unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueBehaviorMinion.BP_RogueBehaviorMinion_C'))
monster.set_editor_property('HealthWidgetClass',unreal.load_class(None,'/Game/DasRogue/UI/WBP_RogueHealth.WBP_RogueHealth_C'))
monster.set_editor_property('LootCoins',LAYOUT['directors'][0]['rows'][0]['LootCoins'])
monster.set_editor_property('Actions',[unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionEffectOverwhelm.BP_RogueActionEffectOverwhelm_C')])
table=unreal.load_asset('/Game/DasRogueExternal/Director/DT_CourseMonsters')
if not table:
    factory=unreal.DataTableFactory();factory.set_editor_property('struct',unreal.load_object(None,'/Game/DasRogue/Types/RogueMonsterSpawnData.RogueMonsterSpawnData'))
    table=tools.create_asset('DT_CourseMonsters','/Game/DasRogueExternal/Director',unreal.DataTable,factory)
rows=[dict(Name=row['Name'],MonsterData=monster.get_path_name(),SpawnCost=row['SpawnCost'],SpawnWeight=row['SpawnWeight']) for row in LAYOUT['directors'][0]['rows']]
assert unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(table,json.dumps(rows))
configs=[]
config_kind=unreal.load_class(None,'/Game/DasRogue/Director/BP_RogueDirectorConfig.BP_RogueDirectorConfig_C')
for index,source in enumerate(LAYOUT['directors']):
    path='/Game/DasRogueExternal/Director/C_Income'+str(index)
    unreal.SystemLibrary.execute_console_command(world,'Das.Curve.ImportText '+path+' '+str(LOCAL/f'income_{index}.txt'))
    curve=unreal.load_asset(path);assert curve
    config=data_asset('DA_Director'+str(index),config_kind)
    for key,value in dict(DisplayName=source['DebugDisplayName'],MonsterSpawnTable=table,SpawnLocationQuery=query,CreditGainCurve=curve,StartingCredits=0.0,TickInterval=float(source['TickInterval']),TimeBetweenWaves=float(source['TimeBetweenWaves'])).items():
        config.set_editor_property(key,value)
    configs.append(config)
# Re-running preparation replaces only our authored actors; native geometry stays intact.
for actor in list(actors.get_all_level_actors()):
    if actor.get_class().get_path_name().startswith('/Game/DasRogue/'):
        actors.destroy_actor(actor)

def rotation(values):
    return unreal.Rotator(pitch=values[0],yaw=values[1],roll=values[2])

def blueprint(path):
    name=path.rsplit('/',1)[-1]
    value=unreal.load_class(None,path+'.'+name+'_C');assert value,path
    return value

classes={
    'BP_Lever':'/Game/DasRogue/World/BP_RogueLever',
    'BP_ProjectileSpammer':'/Game/DasRogue/World/BP_RogueProjectileSpammer',
    'BP_ItemChest':'/Game/DasRogue/World/BP_RogueCourseChest',
    'BP_HealthPickup':'/Game/DasRogue/Pickups/BP_RogueHealthPickup',
    'BP_ExplosiveBarrel':'/Game/DasRogue/World/BP_RogueExplosiveBarrel',
    'MinionRangedBP':'/Game/DasRogue/AI/BP_RogueBehaviorMinion',
    'RoguePatrolPoint':'/Game/DasRogue/AI/BP_RoguePatrolPoint',
    'RogueCoinTestActor':'/Game/DasRogue/Pickups/BP_RogueCoinTestActor',
    'BP_ApplyZone':'/Game/DasRogue/World/BP_RogueCourseStunZone'}
components={'SwitchBaseMeshComp':'SwitchBaseMeshComp','HandleMeshComp':'HandleMeshComp','Sphere':'InteractionSphere',
    'Arrow':'Arrow','BasMeshComp':'BaseMeshComponent','LidMeshComp':'LidMeshComponent','TreasurePileComp':'TreasurePile',
    'TreasureBurstEffectComp':'TreasureBurst','OverlapComp':'OverlapComponent','PickupMeshComp':'PickupMeshComponent',
    'MeshComp':'MeshComponent','RadialForceComp':'RadialForceComponent','Box':'Box'}
MANIFEST=json.loads((ROOT/'ExternalAssets.json').read_text())
created={}
for row in LAYOUT['actors']:
    cls=row['kind'].rsplit('.',1)[-1].removesuffix('_C')
    if cls not in classes:continue
    pose=row['pose']
    actor=actors.spawn_actor_from_class(blueprint(classes[cls]),unreal.Vector(*pose['location']),rotation(pose['rotation']))
    assert actor,row['label']
    actor.set_actor_location(unreal.Vector(*pose['location']),False,True)
    actor.set_actor_label(row['label'])
    actor.set_actor_scale3d(unreal.Vector(*pose['scale']))
    actor.modify(True)
    created[row['label']]=actor
    if cls=='BP_ItemChest':
        actor.set_editor_property('TreasureSound',unreal.load_asset(row['properties']['TreasureBurstSound']))
        actor.set_editor_property('AnimationSpeed',float(row['properties']['AnimationSpeed']))
        actor.set_editor_property('AnimationTargetPitch',float(row['properties']['AnimationTargetPitch']))
    if cls=='BP_ExplosiveBarrel':
        for field in ['BurningEffect','BurningSound','ExplosionEffect','ExplosionSound']:
            actor.set_editor_property(field,unreal.load_asset(MANIFEST['course_world_effects'][field]))
    if cls=='BP_HealthPickup':
        actor.set_editor_property('PickupSound',unreal.load_asset(row['properties']['PickupSound']))
        actor.set_editor_property('HealingAmount',float(row['properties']['HealingAmount']))
        actor.set_editor_property('PickupMaterial',None)
        actor.set_editor_property('RequireInteraction',False)
        actor.set_editor_property('RespawnDelay',0.0)
    if cls=='MinionRangedBP':actor.set_editor_property('MonsterData',unreal.load_asset('/Game/DasRogueExternal/Director/DA_CourseMinion'))
    if cls=='RogueCoinTestActor':
        actor.set_editor_property('CoinSystemClass',blueprint('/Game/DasRogue/Pickups/BP_RogueCoinPickupSubsystem'))
    for source in row['components']:
        field=components.get(source['name'])
        if not field:continue
        try:component=actor.get_editor_property(field)
        except Exception:continue
        if not component:continue
        component.modify(True)
        if component!=actor.root_component:
            component.set_relative_location(unreal.Vector(*(source['location'] if source['parent'] else [0,0,0])),False,True)
            component.set_relative_rotation(rotation(source['rotation'] if source['parent'] else [0,0,0]),False,True)
            component.set_relative_scale3d(unreal.Vector(*(source['scale'] if source['parent'] else [1,1,1])))
        if isinstance(component,unreal.StaticMeshComponent) and source.get('mesh'):
            mesh=unreal.load_asset(source['mesh']);assert mesh,source['mesh']
            component.set_static_mesh(mesh)
            for index,path in enumerate(source.get('materials',[])):
                if path:
                    material=unreal.load_asset(path);assert material,path
                    component.set_material(index,material)
        if isinstance(component,unreal.NiagaraComponent) and source.get('asset'):
            effect=unreal.load_asset(source['asset']);assert effect,source['asset']
            component.set_asset(effect)
        if isinstance(component,unreal.SphereComponent) and source.get('sphere_radius'):
            component.set_sphere_radius(source['sphere_radius'],False)
        if isinstance(component,unreal.BoxComponent) and source.get('box_extent'):
            component.set_box_extent(unreal.Vector(*source['box_extent']),False)
            component.set_collision_profile_name('OverlapAllDynamic')
    if cls=='BP_ItemChest':
        hinge=actor.get_editor_property('LidMeshComponent').get_editor_property('relative_location')
        assert (hinge-unreal.Vector(-35,0,50)).length()<.001,('Chest hinge after construction',hinge)
    if cls=='BP_Lever':actor.get_editor_property('InteractionSphere').set_sphere_radius(200,False)
director=actors.spawn_actor_from_class(blueprint('/Game/DasRogue/Director/BP_RogueSpawnDirector'),unreal.Vector())
director.set_actor_label('Original GameMode directors - daScript')
director.set_editor_property('Configurations',configs)
director.set_editor_property('GlobalStartingSeed',int(LAYOUT['game_mode_defaults']['GlobalStartingSeed']))
director.set_editor_property('BotLimit',5)
director.set_editor_property('AutoStart',False)
logic=actors.spawn_actor_from_class(blueprint('/Game/DasRogue/World/BP_RogueCourseWorld'),unreal.Vector())
logic.set_actor_label('Course Level Blueprint - daScript')
logic.set_editor_property('SpammerLever',created['BP_Lever'])
logic.set_editor_property('CoinLever',created['BP_Lever2'])
logic.set_editor_property('Spammer',created['BP_ProjectileSpammer'])
logic.set_editor_property('CoinSource',created['RogueCoinTestActor'])
logic.set_editor_property('Director',director)
for field in ['CoinMesh','CoinSound']:
    asset=unreal.load_asset(COINS[field]);assert asset,COINS[field]
    logic.set_editor_property(field,asset)
logic.set_editor_property('CoinPickupTrigger',COINS['PickupTrigger'])
# Coin instances require an ISM shader permutation before the first gameplay batch.
coin_material=unreal.load_asset('/Game/DasRogue/Materials/M_TargetHealth')
coin_material.modify(True)
coin_material.set_editor_property('used_with_instanced_static_meshes',True)
course_coin_material=unreal.load_asset('/Game/ExampleContent/Materials/M_Pickup_Coin')
assert course_coin_material
if not course_coin_material.get_editor_property('used_with_instanced_static_meshes'):
    course_coin_material.modify(True)
    course_coin_material.set_editor_property('used_with_instanced_static_meshes',True)
# Validate the source Euler rotations through named Python fields (positional
# Rotator constructor arguments are roll/pitch/yaw, unlike exported pitch/yaw/roll).
for row in LAYOUT['actors']:
    actor=created.get(row['label'])
    if not actor:continue
    actual=actor.get_actor_rotation()
    for value,expected in zip([actual.pitch,actual.yaw,actual.roll],row['pose']['rotation']):
        assert abs((value-expected+180)%360-180)<.001,(row['label'],actual,row['pose']['rotation'])
# Keep all original positions; select the same generic game mode used by the port.
level=next(a for a in actors.get_all_level_actors() if isinstance(a,unreal.PlayerStart)).get_level()
settings=next(a for a in unreal.ObjectIterator(unreal.WorldSettings) if a.get_outer()==level)
settings.set_editor_property('default_game_mode',blueprint('/Game/DasRogue/BP_RogueGameMode'))
nav=next((a for a in actors.get_all_level_actors() if isinstance(a,unreal.RecastNavMesh)),None)
if not nav:nav=actors.spawn_actor_from_class(unreal.RecastNavMesh,unreal.Vector())
nav.set_editor_property('runtime_generation',unreal.RuntimeGenerationType.DYNAMIC)
unreal.SystemLibrary.execute_console_command(world,'RebuildNavigation')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
print('DAS_COURSE_WORLD_PREPARE PASS',len(created),'authored replacements')
