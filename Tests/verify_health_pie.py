"""Run in a fresh ChestTest PIE. Real Enhanced Input and world movement, no synthetic hits."""
import unreal
import json
import time
import traceback
from pathlib import Path

world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert world, "Start PIE first"
player=unreal.GameplayStatics.get_player_controller(world,0)
pawn=unreal.GameplayStatics.get_player_pawn(world,0)
target=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=="BP_TargetDummy_C")
attributes=target.get_editor_property("Attributes")
assert attributes.get_editor_property("Health")==100.0, "Use a fresh PIE"
assert attributes.call_method("IsAlive")
# Clamping, no-op suppression, signed healing and separate component state.
assert not attributes.call_method("ApplyHealthChange",args=(pawn,0.0))
assert attributes.get_editor_property("HealthChanges")==0
assert attributes.call_method("ApplyHealthChange",args=(pawn,-10.0))
assert attributes.get_editor_property("Health")==90.0
assert attributes.call_method("ApplyHealthChange",args=(pawn,1000.0))
assert attributes.get_editor_property("Health")==100.0
assert not attributes.call_method("ApplyHealthChange",args=(pawn,1.0))
assert attributes.get_editor_property("HealthChanges")==2
initial_hits=target.get_editor_property("Hits")
initial_shots=player.get_editor_property("ProjectilesFired")
# Python can retain obsolete LocalPlayers across PIE restarts. Choose the newest instance.
subsystems=[s for s in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if s.get_outer().get_class().get_name()=="LocalPlayer"]
def player_index(s):
    name=s.get_outer().get_name()
    try: return int(name.rsplit("_",1)[-1])
    except ValueError: return -1
input_system=max(subsystems,key=player_index)
action=unreal.load_asset("/Game/DasRogue/Input/IA_Fire")
player.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(pawn.get_actor_location(),target.get_actor_location()))
old_idle=unreal.SystemLibrary.get_console_variable_int_value("t.IdleWhenNotForeground")
unreal.SystemLibrary.execute_console_command(world,"t.IdleWhenNotForeground 0")
result_path=Path("C:/src/ActionRoguelikeDas/Saved/Tests/rogue_health_pie.json")
result_path.parent.mkdir(parents=True,exist_ok=True)
state={"phase":"aim","shot":0,"at":time.perf_counter(),"start":time.perf_counter(),"checks":[],"done":False}

def finish(error=None):
    state["done"]=True
    unreal.unregister_slate_post_tick_callback(state["handle"])
    unreal.SystemLibrary.execute_console_command(world,"t.IdleWhenNotForeground "+str(old_idle))
    result={"passed":error is None,"error":error,"checks":state["checks"],"elapsed_seconds":time.perf_counter()-state["start"]}
    result_path.write_text(json.dumps(result,indent=2),encoding="utf-8")
    unreal.log("DAS_ROGUE_HEALTH_PIE "+json.dumps(result))

def tick(delta):
    if state["done"]: return
    try:
        now=time.perf_counter()
        assert now-state["start"]<60, "Timed out waiting for real input/projectile collisions"
        if state["phase"]=="aim":
            camera=unreal.GameplayStatics.get_player_camera_manager(world,0)
            player.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_camera_location(),target.get_actor_location()))
            if now-state["at"]<0.8: return
            state["phase"]="fire"
        if state["phase"]=="fire":
            input_system.inject_input_vector_for_action(action,unreal.Vector(1,0,0),[],[])
            state["shot"]+=1
            state["phase"]="impact"
            state["at"]=now
            return
        if state["phase"]=="impact":
            expected=100.0-25.0*state["shot"]
            health=attributes.get_editor_property("Health")
            if health!=expected:
                assert now-state["at"]<8, "Expected HP "+str(expected)+", got "+str(health)+"; shots="+str(player.get_editor_property("ProjectilesFired"))
                return
            assert target.get_editor_property("Hits")==initial_hits+state["shot"], "Duplicate/missing health event"
            assert attributes.get_editor_property("HealthChanges")==2+state["shot"]
            assert attributes.get_editor_property("LastInstigator")==pawn, "Damage instigator was not preserved"
            assert str(target.get_editor_property("Label").get_editor_property("text"))=="HP: "+str(int(expected))+" / 100"
            for obj in [target,attributes,player]:
                assert not obj.get_editor_property("LastDasError"), obj.get_editor_property("LastDasError")
            material=target.get_editor_property("Visual").get_material(0)
            assert material.get_class().get_name()=="MaterialInstanceDynamic"
            colors=material.get_editor_property("vector_parameter_values")
            color=next(x.get_editor_property("parameter_value") for x in colors if str(x.get_editor_property("parameter_info").get_editor_property("name"))=="Color")
            assert abs(color.r-(1-expected/100))<0.001 and abs(color.g-expected/100)<0.001, "Wrong health color"
            state["checks"].append({"shot":state["shot"],"health":health,"color":[color.r,color.g,color.b],"instigator":pawn.get_name()})
            if expected==0:
                assert not attributes.call_method("IsAlive")
                assert target.get_editor_property("Dead")
                state["phase"]="death"
            else:
                state["phase"]="release"
            state["at"]=now
            return
        if state["phase"]=="release":
            if now-state["at"]<0.8: return
            assert not [a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if a.get_class().get_name()=="BP_MagicProjectileDemo_C"], "Projectile did not destroy after damage"
            state["phase"]="fire"
            return
        if state["phase"]=="death":
            actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
            if target in actors:
                assert now-state["at"]<8, "Target did not destroy at zero HP"
                return
            assert player.get_editor_property("ProjectilesFired")==initial_shots+4, "One shot per press violated"
            assert not [a for a in actors if a.get_class().get_name()=="BP_MagicProjectileDemo_C"]
            state["checks"].append({"target_destroyed":True,"projectiles_destroyed":True,"shots":4,"clamp_and_noop":True})
            finish()
    except Exception:
        finish(traceback.format_exc())

state["handle"]=unreal.register_slate_post_tick_callback(tick)
unreal._rogue_health_verification=state
print("Health integration test scheduled")
