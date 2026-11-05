"""Original map geometry and input-driven level bindings in real PIE."""
from pathlib import Path
import unreal,json,time,traceback,math
ROOT=Path(__file__).resolve().parents[1]
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
def prop(o,n):return o.get_editor_property(n)
def now():return unreal.GameplayStatics.get_time_seconds(world)
def live(o):return o is not None and unreal.SystemLibrary.is_valid(o)
all_actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
by_label={a.get_actor_label():a for a in all_actors}
player=unreal.GameplayStatics.get_player_controller(world,0)
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
system=prop(pawn,'ActionSystem')
pawn.character_movement.disable_movement()
logic=by_label['Course Level Blueprint - daScript']
spammer=by_label['BP_ProjectileSpammer']
coins=next(o for o in unreal.ObjectIterator(unreal.load_class(None,'/Game/DasRogue/Pickups/BP_RogueCoinPickupSubsystem.BP_RogueCoinPickupSubsystem_C')) if o.get_outer()==world)
inputs=max([v for v in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if v.get_outer().get_class().get_name()=='LocalPlayer'],key=lambda v:int(v.get_outer().get_name().rsplit('_',1)[-1]))
s=dict(done=False,phase='patrol',at=now(),started=time.perf_counter(),checks=[],enemy_origin=by_label['MinionRangedBP'].get_actor_location())
def inject(name):inputs.inject_input_vector_for_action(unreal.load_asset('/Game/DasRogue/Input/'+name),unreal.Vector(1,0,0),[],[])
def move(x,y,z=102):pawn.set_actor_location(unreal.Vector(x,y,z),False,True);player.set_control_rotation(unreal.Rotator())
def phase(n):s.update(phase=n,at=now())
def check(n):s['checks'].append(n)
def finish(error=None):
 s['done']=True;unreal.unregister_slate_post_tick_callback(s['handle'])
 (ROOT/'Saved/Tests/rogue_course_world_pie.json').write_text(json.dumps(dict(passed=error is None,error=error,checks=s['checks']),indent=2))
def tick(delta):
 if s['done']:return
 try:
  assert time.perf_counter()-s['started']<65,s['phase']
  for obj in [player,pawn,logic,spammer,coins]:
   if live(obj):assert not prop(obj,'LastDasError'),prop(obj,'LastDasError')
  age=now()-s['at']
  if s['phase']=='patrol':
   enemy=by_label['MinionRangedBP'];controller=enemy.get_controller();assert controller
   points=[a for a in all_actors if 'PatrolPoint' in a.get_class().get_name()]
   assert len(points)==6
   if not all(prop(p,'ConnectionsReady') for p in points) or (enemy.get_actor_location()-s['enemy_origin']).length()<80:
    assert age<12,'Course patrol did not initialize and move without a manual graph rebuild'
    return
   board=prop(controller,'blackboard');brain=prop(controller,'brain_component')
   assert brain.is_running() and not brain.is_paused()
   assert not board.get_value_as_object('TargetActor')
   assert board.get_value_as_object('CurrentPatrolPoint') in points
   # All six original points are connected on the correct Flat Middle.
   # The old doubled terrain incorrectly isolated the sixth point. Explicit
   # off-navmesh fixture coverage belongs to verify_behavior_tree_pie.py.
   assert all(len(prop(p,'NearbyPatrolPoints'))>0 for p in points)
   controller.set_editor_property('BrainEnabled',False)
   controller.stop_movement()
   check('course_six_point_patrol_initializes_and_moves_without_test_bootstrap')
   check('all_six_course_patrol_points_connect_on_original_flat_middle')
   phase('ready');return
  if s['phase']=='ready':
   if age<.5:return
   assert len([a for a in all_actors if a.get_class().get_path_name()=='/Script/Landscape.LandscapeStreamingProxy'])==64
   assert abs(pawn.get_actor_location().x+1220)<1 and abs(pawn.get_actor_location().y-480)<1
   assert prop(player,'ControlsBound') and prop(pawn,'ControlsBound')
   assert prop(prop(player,'HUD'),'HUD').is_in_viewport()
   for actor in all_actors:assert not actor.get_class().get_path_name().startswith('/Script/ActionRoguelike.')
   # Actor transforms alone missed the doubled edit-layer surface. Compare
   # collision against independently decoded original merged heightmaps.
   reference=json.loads((ROOT/'Saved/ExternalAssets/course_world/landscape_surface_reference.json').read_text())
   assert len(reference)==256
   ignore=[a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if not isinstance(a,unreal.LandscapeProxy)]
   terrain_errors=[]
   for point in reference:
    hits=unreal.SystemLibrary.line_trace_multi(world,unreal.Vector(point['x'],point['y'],50000),unreal.Vector(point['x'],point['y'],-50000),unreal.TraceTypeQuery.ECC_VISIBILITY,True,ignore,unreal.DrawDebugTrace.NONE,True)
    height=hits[0].to_dict()['impact_point'].z if hits else None
    if height is None or abs(height-point['z'])>1:terrain_errors.append((point,height))
   assert not terrain_errors,terrain_errors[:3]
   check('all_256_landscape_components_match_original_merged_surface')
   source=json.loads((ROOT/'Saved/ExternalAssets/course_world/layout.json').read_text())
   for row in source['actors']:
    actor=by_label.get(row['label'])
    if actor and row['kind']!='/Script/Engine.WorldPartitionMiniMap' and 'Barrel' not in row['kind'] and 'MinionRanged' not in row['kind']:
     if any(c.is_simulating_physics() for c in actor.get_components_by_class(unreal.PrimitiveComponent)):continue
     expected=unreal.Vector(*row['pose']['location'])
     assert (actor.get_actor_location()-expected).length()<2,(row['label'],actor.get_actor_location(),expected)
     actual=actor.get_actor_rotation()
     for angle,wanted in zip([actual.pitch,actual.yaw,actual.roll],row['pose']['rotation']):
      assert abs((angle-wanted+180)%360-180)<.001,(row['label'],actual,row['pose']['rotation'])
   for row in source['actors']:
    if 'LandscapeStreamingProxy' not in row['kind']:continue
    actor=by_label[row['label']]
    parts={c.get_name():c for c in actor.get_components_by_class(unreal.SceneComponent)}
    for original in row['components']:
     component=parts.get(original['name']);assert component,original['name']
     assert (component.get_world_location()-unreal.Vector(*original['world_location'])).length()<.1,(row['label'],original['name'],'world location')
     assert (component.get_world_scale()-unreal.Vector(*original['world_scale'])).length()<.001,(row['label'],original['name'],'world scale')
   enemy=by_label['MinionRangedBP'];controller=enemy.get_controller();assert controller
   controller.set_editor_property('BrainEnabled',False)
   check('original_spawn_and_all_64_landscape_sections_with_DAS_player_HUD_and_actor_positions')
   move(780,-670);phase('spammer_aim');return
  if s['phase']=='spammer_aim':
   if age<.2:return
   inject('IA_Interact');phase('spammer');return
  if s['phase']=='spammer':
   if age<.8:return
   assert prop(logic,'SpammerStarts')==1 and prop(logic,'CoinBatches')==0
   assert prop(spammer,'ProjectilesSpawned')>=1
   assert prop(prop(spammer,'LastProjectile'),'instigator')==spammer
   spammer.call_method('StopSpawning',args=())
   check('first_original_lever_starts_native_projectile_spammer_only')
   move(780,-220);phase('coin_aim');return
  if s['phase']=='coin_aim':
   if age<.2:return
   inject('IA_Interact');phase('coins');return
  if s['phase']=='coins':
   if age<.5:return
   assert prop(logic,'CoinBatches')==1 and prop(logic,'SpammerStarts')==1
   assert prop(coins,'CoinCount')+prop(coins,'CollectedValue')//10==1000
   assert prop(coins,'WorldISM')
   check('second_original_lever_creates_1000_batched_coins_without_coin_actors')
   renderer=prop(coins,'WorldISM')
   mesh=renderer.get_editor_property('static_mesh')
   assert mesh.get_path_name()=='/Game/ExampleContent/Meshes/SM_Pickup_Coin.SM_Pickup_Coin'
   assert renderer.get_material(0)==mesh.get_material(0)
   assert renderer.get_material(0).get_editor_property('used_with_instanced_static_meshes')
   assert not prop(coins,'CoinMaterial')
   assert (prop(coins,'MeshScale')-unreal.Vector(1,1,1)).length()<.001
   assert (prop(coins,'VisualOffset')-unreal.Vector(0,0,50)).length()<.001
   first=renderer.get_instance_transform(0,True)
   assert (first.scale3d-unreal.Vector(1,1,1)).length()<.001
   assert abs(first.rotation.x)+abs(first.rotation.y)+abs(first.rotation.z)<.001
   assert prop(coins,'CoinSound').get_path_name().endswith('MSS_Interactables_CurrencyPickup.MSS_Interactables_CurrencyPickup')
   assert prop(coins,'PickupTrigger')=='CoinPickedUp'
   check('original_u_logo_coin_mesh_material_unit_scale_and_pickup_audio')
   chest=by_label['BP_ItemChest'];move(1075,-1075);s['chest']=chest;phase('chest_aim');return
  if s['phase']=='chest_aim':
   if age<.2:return
   inject('IA_Interact');phase('chest');return
  if s['phase']=='chest':
   chest=s['chest']
   if prop(chest,'CurrentAnimationPitch')<119.9:
    assert age<4,'Original chest did not animate';return
   assert prop(chest,'BaseMeshComponent').get_editor_property('static_mesh').get_path_name().endswith('SM_Chest_Bottom.SM_Chest_Bottom')
   hinge=prop(chest,'LidMeshComponent').get_editor_property('relative_location')
   assert (hinge-unreal.Vector(-35,0,50)).length()<.001,('animated hinge',repr(hinge.x),repr(hinge.y),repr(hinge.z))
   check('original_chest_meshes_and_rear_hinge_open_through_real_E_input')
   assert prop(chest,'TreasureSound')
   attributes=prop(pawn,'Attributes')
   assert attributes.call_method('ApplyHealthChange',args=(pawn,-75.0))
   s['expected_health']=min(prop(attributes,'HealthMax'),prop(attributes,'Health')+prop(by_label['BP_HealthPickup'],'HealingAmount'))
   move(510,-1040);phase('healing');return
  if s['phase']=='healing':
   if age<.4:return
   assert prop(prop(pawn,'Attributes'),'Health')==s['expected_health']
   assert prop(by_label['BP_HealthPickup'],'Collections')==1
   check('original_potion_overlap_heals_and_consumes_once')
   assert prop(coins,'CoinCount')>0
   location=coins.call_method('LocationAt',args=(0,))
   s['wallet']=prop(system,'Coins')
   move(location.x,location.y,max(location.z+88,102));phase('collection');return
  if s['phase']=='collection':
   if prop(system,'Coins')<=s['wallet']:
    assert age<3,'Nearby batched coin did not reach the wallet';return
   assert prop(system,'Coins')==prop(coins,'CollectedValue')
   assert prop(coins,'WorldAudio')
   check('world_coins_collect_into_the_int64_player_wallet')
   s['coin_total']=prop(coins,'RemainingValue')+prop(coins,'CollectedValue')
   unreal.GameplayStatics.apply_damage(by_label['MinionRangedBP'],1000.0,player,pawn,None)
   phase('loot');return
  if s['phase']=='loot':
   enemy=by_label['MinionRangedBP']
   if not prop(enemy,'Dead'):
    assert age<3,'Placed minion did not die';return
   assert prop(enemy,'LootDrops')==1 and prop(enemy,'LastLootCoins')==100
   assert prop(coins,'RemainingValue')+prop(coins,'CollectedValue')==s['coin_total']+100
   check('placed_course_minion_uses_original_MonsterData_and_drops_100_coins')
   move(-1220,480)
   s['query']=unreal.EnvQueryManager.run_eqs_query(world,unreal.load_asset('/Game/DasRogueExternal/Director/EQS_FindMonsterSpawn'),pawn,unreal.EnvQueryRunMode.SINGLE_RESULT,None)
   assert s['query']
   phase('query');return
  if s['phase']=='query':
   locations=s['query'].get_query_results_as_locations()
   if isinstance(locations,tuple):locations=locations[-1] if locations[0] else []
   if not locations:
    assert age<5,'Original native EQS with the DAS alive-player context returned no location';return
   origin=pawn.get_actor_location();point=locations[0]
   assert (point-origin).length()>=1000,(point,origin)
   check('original_native_donut_distance_and_path_query_uses_DAS_alive_player_array_context')
   finish()
 except Exception:finish(traceback.format_exc())
s['handle']=unreal.register_slate_post_tick_callback(tick)
