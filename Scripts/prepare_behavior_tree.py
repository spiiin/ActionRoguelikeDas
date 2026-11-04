"""Prepare native BT/EQS assets with DAS custom nodes; retain a separate inspection map."""
from pathlib import Path
import runpy
import unreal
ROOT=Path(__file__).resolve().parents[1]
# Core game assets are versioned; only this stage's changed dependency needs reimport.
setup_world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(setup_world,'Das.DSL.Reimport /Game/DasRogue/Actions/BP_RogueActionProjectileAttack')
runpy.run_path(str(ROOT/'Scripts/prepare_action_tests.py'))
runpy.run_path(str(ROOT/'Scripts/prepare_ai.py'))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
nodes=['RogueBTHealSelf','RogueBTLowHealth','RogueBTCheckRange','RogueBTRangedAttack','RogueBTFindPatrol','RogueEQSTarget']
for name in nodes:
    path='/Game/DasRogue/AI/BT/BP_'+name
    command=('Das.DSL.Reimport '+path if assets.does_asset_exist(path) else 'Das.DSL.Apply rogue_bt_tasks.das '+path+' rogue.'+name)
    unreal.SystemLibrary.execute_console_command(world,command)
    assert unreal.load_class(None,path+'.BP_'+name+'_C'),name+' failed to import'
for name,kind in [('MinionRangedBB','BlackboardData'),('EQS_TargetSelection','EnvQuery'),('EQS_MoveToTarget','EnvQuery'),('EQS_MoveToCover','EnvQuery'),('MinionRangedBT','BehaviorTree')]:
    package='/Game/DasRogue/AI/BT/'+name
    if not assets.does_asset_exist(package):
        unreal.SystemLibrary.execute_console_command(world,'Das.AI.ImportText /Script/AIModule.'+kind+' '+package+' '+str(ROOT/'Scripts/ai_assets'/ (name+'.t3d')))
    assert unreal.load_asset(package),'AI asset import failed: '+name
path='/Game/DasRogue/AI/BP_RogueBehaviorController'
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Reimport '+path if assets.does_asset_exist(path) else 'Das.DSL.Apply rogue_behavior_controller.das '+path+' rogue.RogueBehaviorController')
controller=unreal.load_class(None,path+'.BP_RogueBehaviorController_C')
assert controller
unreal.load_asset(path).modify(True)
unreal.get_default_object(controller).set_editor_property('BehaviorTree',unreal.load_asset('/Game/DasRogue/AI/BT/MinionRangedBT'))
minion_path='/Game/DasRogue/AI/BP_RogueBehaviorMinion'
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_behavior_minion.das '+minion_path+' roguedemo.RogueBehaviorMinion')
assert unreal.load_class(None,minion_path+'.BP_RogueBehaviorMinion_C')
runpy.run_path(str(ROOT/'Scripts/prepare_patrol.py'))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem) or unreal.get_default_object(unreal.LevelEditorSubsystem)
map_path='/Game/DasRogue/Maps/BehaviorTest'
if not assets.does_asset_exist(map_path): assert level.new_level_from_template(map_path,'/Game/DasRogue/Maps/PatrolTest')
else: assert level.load_level(map_path)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
point_kind=unreal.load_class(None,'/Game/DasRogue/AI/BP_RoguePatrolPoint.BP_RoguePatrolPoint_C')
kind=unreal.load_class(None,'/Game/DasRogue/AI/BT/BP_RogueBTFindPatrol.BP_RogueBTFindPatrol_C')
unreal.load_asset('/Game/DasRogue/AI/BT/BP_RogueBTFindPatrol').modify(True)
unreal.get_default_object(kind).set_editor_property('PatrolPointClass',point_kind)
for actor in actors.get_all_level_actors():
    if actor.get_class().get_name()=='BP_RogueAICharacter_C':
        actor.set_editor_property('ai_controller_class',controller)
        actor.set_actor_label('daScript Minion - native BT and EQS')
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
# The persistent patrol template intentionally contains no test probe.
probe_kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueActionProbe.BP_RogueActionProbe_C')
assert probe_kind
assert actors.spawn_actor_from_class(probe_kind,unreal.Vector(0,0,-1000))
print('DAS_BEHAVIOR_PREPARE PASS')
