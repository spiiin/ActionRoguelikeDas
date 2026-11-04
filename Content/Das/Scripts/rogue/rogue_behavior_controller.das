options gen2
module rogue_behavior_controller public
require rogue_ai_controller public
require ue_behavior_tree public

// Native BT/EQS scheduling; all custom tasks, conditions and contexts execute DAS.
[ue_class(module_id="rogue", Blueprintable)]
class RogueBehaviorController : RogueAIController {
    @ue_property=(EditAnywhere, BlueprintReadWrite)
    BehaviorTree:ObjectRef

    state=ue_properties(BlueprintReadWrite) {
        var TreeStarted:bool=false
        var TreePaused:bool=false
        var TreeStopped:bool=false
    }

    def override Tick(delta:float):void {
        let ai=ue_ai_self_controller()
        let pawn=ue_ai_pawn(ai)
        if (!ue_is_valid(pawn)) { return }
        let enemy=ue_ref(type<RogueAICharacterRef>,pawn.handle)
        if (!self.BrainEnabled || enemy.Dead) {
            if (self.TreeStarted && !self.TreeStopped) { ue_ai_brain(ai,"StopLogic","Stopped"); self.TreeStopped=true }
            return
        }
        if (!self.TreeStarted) {
            // Configure the native listener once the controller possesses its pawn,
            // before starting EQS. Keep the inherited lifecycle graph unchanged.
            ue_perception_configure(self.Perception,self.SightRadius,self.LoseSightRadius,
                self.SightAngle,self.HearingRadius,self.TargetMemory,true,false,false)
            if (ue_is_valid(self.BehaviorTree)) { self.TreeStarted=ue_ai_run_behavior_tree(ai,self.BehaviorTree) }
            return
        }
        if (self.TreePaused!=enemy.Stunned) {
            if (ue_ai_brain_pause(ai,enemy.Stunned,"Gameplay stun")) { self.TreePaused=enemy.Stunned }
        }
        // EQS selects from native perception; do not run the earlier direct chase thinker.
        let board=ue_ai_blackboard(ai)
        let target=ue_blackboard_object(board,"TargetActor")
        if (ue_is_valid(target) && !self.IsLivePlayer(target)) {
            ue_blackboard_set_object(board,"TargetActor",default<ActorRef>)
            ue_blackboard_set_bool(board,"WithinRange",false)
            enemy.Target=default<ActorRef>
        }
        self.CurrentTarget=ue_blackboard_object(board,"TargetActor")
    }

    def override EndPlay(reason:int):void {
        // Native AAIController teardown stops its BrainComponent and behavior tree.
        // Managed AI operations require a live session, which EndPlay has ended.
        self.TreeStopped=true
        Super.EndPlay(reason)
    }
}

typedef RogueBehaviorControllerRef=UEObjectRef("rogue.RogueBehaviorController")
