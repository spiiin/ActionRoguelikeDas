"""Build a separate NavMesh arena; gameplay and patrol graph execute in DAS."""
import unreal

editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem) or unreal.get_default_object(unreal.LevelEditorSubsystem)
assert not editor.get_game_world(),'Prepare outside PIE'
world=editor.get_editor_world()
for command in [
    'Das.DSL.Apply rogue_patrol_point.das /Game/DasRogue/AI/BP_RoguePatrolPoint rogue.RoguePatrolPoint',
    'Das.DSL.Apply rogue_patrol_controller.das /Game/DasRogue/AI/BP_RoguePatrolController rogue.RoguePatrolController',
]:
    unreal.SystemLibrary.execute_console_command(world,command)
point_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RoguePatrolPoint.BP_RoguePatrolPoint_C')
controller_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RoguePatrolController.BP_RoguePatrolController_C')
enemy_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RogueAICharacter.BP_RogueAICharacter_C')
assert point_kind and controller_kind and enemy_kind,'Patrol import failed'
unreal.load_asset('/Game/DasRogue/AI/BP_RoguePatrolController').modify(True)
unreal.get_default_object(controller_kind).set_editor_property('PatrolPointClass',point_kind)

map_path='/Game/DasRogue/Maps/PatrolTest'
if not unreal.get_editor_subsystem(unreal.EditorAssetSubsystem).does_asset_exist(map_path):
    assert level.new_level_from_template(map_path,'/Game/DasRogue/Maps/ChestTest')
elif world.get_name()!='PatrolTest':
    assert level.load_level(map_path)
world=editor.get_editor_world()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
existing=actors.get_all_level_actors()
for actor in list(existing):
    if isinstance(actor,unreal.PlayerStart):
        actor.set_actor_location(unreal.Vector(600,-1500,96),False,True)
    if actor.get_class().get_name()=='BP_RogueActionProbe_C':
        actors.destroy_actor(actor)

positions={'A':(3200,0,10),'B':(4400,0,10),'C':(4400,1200,10),'D':(3200,1200,10)}
for name,xyz in positions.items():
    label='Patrol point '+name
    point=next((a for a in existing if a.get_actor_label()==label),None)
    if not point:point=actors.spawn_actor_from_class(point_kind,unreal.Vector(*xyz))
    point.set_actor_label(label)
    point.set_editor_property('MaxPathLength',2300.0)

obstacle=next((a for a in existing if a.get_actor_label()=='Patrol route obstacle'),None)
if not obstacle:
    obstacle=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(3800,0,150))
    obstacle.set_actor_label('Patrol route obstacle')
    obstacle.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    obstacle.set_actor_scale3d(unreal.Vector(2,8,3))

bounds=next((a for a in existing if isinstance(a,unreal.NavMeshBoundsVolume)),None)
if not bounds:
    bounds=actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume,unreal.Vector(3000,0,200))
    bounds.set_actor_label('Patrol arena navigation bounds')
    bounds.set_actor_scale3d(unreal.Vector(30,22,5))
origin,extent=bounds.get_actor_bounds(False)
assert extent.x>2000 and extent.y>1500,f'Navigation brush has no usable volume: {extent}'

enemies=[a for a in actors.get_all_level_actors() if a.get_class()==enemy_kind]
enemy=enemies[0] if enemies else actors.spawn_actor_from_class(enemy_kind,unreal.Vector(3200,0,96))
for other in enemies[1:]:actors.destroy_actor(other)
enemy.set_actor_location(unreal.Vector(3200,0,96),False,True)
enemy.set_editor_property('ai_controller_class',controller_kind)
enemy.set_editor_property('auto_possess_ai',unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
enemy.set_actor_label('daScript Minion - patrol and combat')

# The fallback cone is disabled in BeginPlay. Keep it out of the editor NavMesh
# too, so it cannot carve a stationary hole at the patrol's starting point.
enemy.get_editor_property('Visual').set_collision_profile_name('NoCollision')

nav_data=next(iter(unreal.GameplayStatics.get_all_actors_of_class(world,unreal.RecastNavMesh)),None)
if not nav_data:
    nav_data=actors.spawn_actor_from_class(unreal.RecastNavMesh,unreal.Vector(3000,0,0))
assert nav_data,'Recast navigation data was not created'
nav_data.set_editor_property('runtime_generation',unreal.RuntimeGenerationType.DYNAMIC)


unreal.SystemLibrary.execute_console_command(world,'RebuildNavigation')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
print('DAS_PATROL_PREPARE PASS',bounds.get_actor_bounds(False))
