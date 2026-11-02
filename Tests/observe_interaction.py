# Optional editor-only probe; no game behavior or synthetic input.
import unreal
import time
import json
from pathlib import Path

last_time=0.0
last_state=None
def observe_interaction(delta):
    global last_time,last_state
    now=time.monotonic()
    if now-last_time<0.5:
        return
    last_time=now
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:
        return
    player=unreal.GameplayStatics.get_player_controller(world,0)
    if not player:
        return
    state={"controller":player.get_class().get_path_name()}
    if "BP_RoguePlayerController" in state["controller"]:
        for name in ["ControlsBound","FireBound","ProjectilesFired","InteractPresses","SuccessfulInteractions","LastDasError"]:
            state[name]=player.get_editor_property(name)
        component=player.get_editor_property("InteractionComponent")
        target=component.get_editor_property("SelectedActor")
        state["SelectedActor"]=target.get_name() if target else None
        state["CandidateCount"]=component.get_editor_property("CandidateCount")
        state["chests"]=[{"actor":actor.get_name(),"pitch":actor.get_editor_property("CurrentAnimationPitch")}
            for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
            if "BP_InteractiveChest" in actor.get_class().get_path_name()]
    if state!=last_state:
        last_state=state
        Path(r"C:/src/ActionRoguelikeDas/Saved/interaction-observation.json").write_text(json.dumps(state,indent=2),encoding="utf-8")
        unreal.log("DAS_ROGUE_EDITOR_OBSERVATION "+json.dumps(state))

probe_handle=unreal.register_slate_post_tick_callback(observe_interaction)
