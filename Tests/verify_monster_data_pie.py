"""Data-driven class/actions/loot; actual DAS spawn and native GC."""
import json,time,traceback
from pathlib import Path
import unreal
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
base=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
kind=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueMonsterProbe.BP_RogueMonsterProbe_C')
probe=base.call_method('Spawn',args=(kind,unreal.Vector(0,0,1000),unreal.Rotator()))
spawner=probe.get_editor_property('Spawner')
data=unreal.load_asset('/Game/DasRogue/AI/DA_RangedMinion')
assert data
checks=[]
def alive(obj):
    try:return unreal.SystemLibrary.is_valid(obj)
    except TypeError as error:
        if 'NativizeObject' in str(error):return False
        raise
def spawn(d,where):return spawner.call_method('SpawnMonster',args=(d,where,unreal.Rotator()))
assert spawn(None,unreal.Vector()) is None
checks.append('null_profile_is_rejected_without_spawning')
invalid=unreal.new_object(data.get_class(),outer=probe)
invalid.set_editor_property('MonsterClass',unreal.Pawn.static_class())
assert spawn(invalid,unreal.Vector()) is None
checks.append('incompatible_monster_class_is_rejected_before_spawn')
enemy=spawn(data,unreal.Vector(3000,800,96));assert enemy
assert enemy.get_class()==data.get_editor_property('MonsterClass')
system=enemy.get_editor_property('ActionSystem')
assert enemy.get_editor_property('MonsterData')==data and enemy.get_editor_property('AppliedMonsterData')==data
assert enemy.get_editor_property('DataActionsGranted')==1
checks.append('profile_selects_class_and_grants_actions_after_initialization')
before=list(system.get_editor_property('Actions'))
assert enemy.call_method('ConfigureMonsterData',args=(data,))
assert list(system.get_editor_property('Actions'))==before and enemy.get_editor_property('DataActionsGranted')==1
checks.append('reapplying_same_profile_does_not_duplicate_actions')
unreal.SystemLibrary.collect_garbage()
assert all(alive(a) for a in before)
checks.append('granted_actions_survive_GC_with_reflected_ownership')
def tag(name):
    t=unreal.GameplayTag();assert t.import_text(name);return t
system.call_method('ApplyAttributeChange',args=(tag('Attribute.Health'),-10000.0))
assert enemy.get_editor_property('Dead') and enemy.get_editor_property('LootDrops')==1
assert enemy.get_editor_property('LastLootCoins')==100
checks.append('profile_granted_DropLoot_runs_on_death_with_profile_coins')
second=spawn(data,unreal.Vector(4000,800,96));assert second
controller=second.get_controller();assert controller
spawner.call_method('ClearMonsters')
assert not alive(second) and not alive(controller)
assert len(spawner.get_editor_property('SpawnedMonsters'))==0
checks.append('clear_destroys_owned_monsters_and_their_controllers')
third=spawn(data,unreal.Vector(4000,800,96));assert third
third_controller=third.get_controller()
probe.destroy_actor()
assert not alive(third) and not alive(third_controller)
checks.append('spawner_EndPlay_cleans_its_owned_actors')
result=Path(unreal.Paths.project_saved_dir())/'Tests/rogue_monster_data_pie.json'
result.write_text(json.dumps({'passed':True,'checks':checks},indent=2))
s={'done':True}
