from pathlib import Path
import runpy
import shutil
import unreal

root=Path(__file__).resolve().parents[1]
for filename in ['prepare_coins.py','prepare_character.py','prepare_ai.py','prepare_patrol.py','prepare_action_tests.py']:
    runpy.run_path(str(root/'Scripts'/filename))
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
drop_kind=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionDropLoot.BP_RogueActionDropLoot_C')
enemy_asset=unreal.load_asset('/Game/DasRogue/AI/BP_RogueAICharacter')
enemy_asset.modify(True)
unreal.get_default_object(enemy_asset.generated_class()).set_editor_property('DropLootActionClass',drop_kind)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in actors.get_all_level_actors():
    if actor.get_class()==enemy_asset.generated_class():actor.set_editor_property('DropLootActionClass',drop_kind)
system_kind=unreal.load_class(None,'/Game/DasRogue/Pickups/BP_RogueCoinPickupSubsystem.BP_RogueCoinPickupSubsystem_C')
spawn_kind=unreal.load_class(None,'/Game/DasRogue/Pickups/BP_RogueCoinTestActor.BP_RogueCoinTestActor_C')
spawner=next((a for a in actors.get_all_level_actors() if a.get_class()==spawn_kind),None)
if not spawner:spawner=actors.spawn_actor_from_class(spawn_kind,unreal.Vector(3200,1200,10))
spawner.set_editor_property('CoinSystemClass',system_kind)
spawner.set_actor_label('daScript coin batch generator')
shutil.copyfile(root/'Tests/Das/roguetest/rogue_coin_probe.das',root/'Content/Das/Scripts/roguetest/rogue_coin_probe.das')
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_coin_probe.das /Game/DasRogue/Tests/BP_RogueCoinProbe roguetest.RogueCoinProbe')
probe_asset=unreal.load_asset('/Game/DasRogue/Tests/BP_RogueCoinProbe')
assert probe_asset
probe_asset.modify(True)
unreal.get_default_object(probe_asset.generated_class()).set_editor_property('CoinSystemClass',system_kind)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
