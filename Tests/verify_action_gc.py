import unreal,gc,json
from pathlib import Path
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
p=unreal.GameplayStatics.get_player_pawn(w,0)
system=p.get_editor_property('ActionSystem')
probe=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_RogueActionProbe_C')
base=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueAction.BP_RogueAction_C')
def collect():
    gc.collect()
    unreal.collect_garbage()
def grant_and_watch():
    a=system.call_method('GrantAction',args=(base,))
    assert a and a.get_outer()==system
    probe.call_method('Watch',args=(a,))
grant_and_watch()
collect()
assert probe.call_method('WatchAlive'),'Reflected array did not retain action'
checks={'strong_reflected_array_survives_gc':True}
probe.call_method('CreateOrphan',args=(base,system))
assert probe.call_method('WatchAlive')
collect()
assert not probe.call_method('WatchAlive'),'Outer retained orphan'
checks['outer_alone_does_not_retain']=True
def remove_and_watch():
    a=system.get_editor_property('Actions')[0]
    probe.call_method('Watch',args=(a,))
    assert system.call_method('RemoveAction',args=(a,))
remove_and_watch()
collect()
assert not probe.call_method('WatchAlive'),'Removed action retained'
checks['removed_action_collected']=True
path=Path('C:/src/ActionRoguelikeDas/Saved/Tests/rogue_actions_gc.json')
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps({'passed':True,'checks':checks},indent=2),encoding='utf-8')
print('DAS_ACTION_GC_PASS',json.dumps(checks))
