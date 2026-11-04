options gen2
module rogue_ai_controller public
require rogue_ai_character public
require ue_perception public
require math
require daslib/match

// Perception and ranged combat slice of RogueAIController; no BehaviorTree asset is required.
[ue_class(module_id="rogue", Blueprintable)]
class RogueAIController : AIController {
    @ue_component
    Perception : PerceptionComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="AI") {
        var SightRadius : float = 1400.0f
        var LoseSightRadius : float = 1700.0f
        var SightAngle : float = 70.0f
        var HearingRadius : float = 1800.0f
        var TargetMemory : float = 3.0f
        var AttackRange : float = 650.0f
        var ThinkInterval : float = 0.15f
        // The open ChestTest arena uses direct movement. Enable with a built NavMesh.
        var UsePathfinding : bool = false
    }

    state = ue_properties(BlueprintReadWrite) {
        var CurrentTarget : ActorRef
        var LastKnownLocation : UEVector
        var LastSensedAt : double = -1.0lf
        var NextThink : double = 0.0lf
        var BrainEnabled : bool = true
        var SightEvents : int = 0
        var HearingEvents : int = 0
        var MoveRequests : int = 0
        var MovesCompleted : int = 0
        var AttackRequests : int = 0
    }

    def BeginPlay() : void {
        ue_controller_set_team(ue_ai_self_controller(),0)
        ue_perception_configure(self.Perception,self.SightRadius,self.LoseSightRadius,
            self.SightAngle,self.HearingRadius,self.TargetMemory)
        ue_perception_configure_damage(self.Perception,self.TargetMemory)
    }

    def BindEvents() : void {
        self.Perception.OnTargetPerceptionUpdated += self.OnPerception
    }

    def IsLivePlayer(target:ActorRef) : bool {
        if (!ue_is_valid(target) || !ue_object_is_a(target.handle,"/Script/Engine.Pawn")) { return false }
        let pawn = ue_ref(type<NativePawnRef>,target.handle)
        if (!pawn.IsPlayerControlled()) { return false }
        let attributes = ue_component_find(type<RogueAttributeComponentRef>,target)
        return ue_is_valid(attributes) && attributes.IsAlive()
    }

    def OnPerception(target:ActorRef; stimulus:AIStimulus) : void {
        if (!self.BrainEnabled || !stimulus.SuccessfullySensed || !self.IsLivePlayer(target)) { return }
        let pawn = ue_ai_pawn(ue_ai_self_controller())
        if (!ue_is_valid(pawn)) { return }
        let enemy = ue_ref(type<RogueAICharacterRef>,pawn.handle)
        if (enemy.Dead) { return }
        match (stimulus.Sense) {
            if (AISense.Sight) { self.SightEvents += 1 }
            if (AISense.Hearing) { self.HearingEvents += 1 }
            if (AISense.Damage) {}
            if (_) { return }
        }
        enemy.Target = target
        self.CurrentTarget = target
        self.LastKnownLocation = stimulus.StimulusLocation
        self.LastSensedAt = ue_world_seconds()
    }

    def Tick(delta:float) : void {
        if (!self.BrainEnabled || ue_world_seconds() < self.NextThink) { return }
        self.NextThink = ue_world_seconds()+double(max(self.ThinkInterval,0.05f))
        let ai = ue_ai_self_controller()
        let pawn = ue_ai_pawn(ai)
        if (!ue_is_valid(pawn)) { return }
        let enemy = ue_ref(type<RogueAICharacterRef>,pawn.handle)
        if (enemy.Dead || enemy.Stunned) {
            ue_ai_move_cancel("Chase")
            return
        }
        let target = enemy.Target
        if (!self.IsLivePlayer(target)) { self.ForgetTarget(); return }
        let origin = ue_ref(type<ActorRef>,pawn.handle).K2_GetActorLocation()
        let distance = length(target.K2_GetActorLocation()-origin)
        let visible = distance <= double(self.LoseSightRadius) && ue_ai_line_of_sight(ai,target)
        if (!visible) { enemy.ActionSystem.StopAction(ue_tag("Action.PrimaryAttack")) }
        if (visible) {
            self.LastSensedAt = ue_world_seconds()
            self.LastKnownLocation = target.K2_GetActorLocation()
        } elif (ue_world_seconds()-self.LastSensedAt > double(self.TargetMemory)) {
            self.ForgetTarget()
            return
        }
        if (visible && distance <= double(self.AttackRange)) {
            ue_ai_move_cancel("Chase")
            ue_ai_set_focus(ai,target)
            if (enemy.ActionSystem.StartAction(ue_tag("Action.PrimaryAttack"))) { self.AttackRequests += 1 }
        } elif (!ue_ai_move_active("Chase")) {
            ue_ai_set_focus(ai,visible ? target : default<ActorRef>)
            if (visible) {
                ue_ai_move_to_actor("Chase",ai,target,self.OnMoveCompleted,60.0f,self.UsePathfinding,true)
            } else {
                ue_ai_move_to_location("Chase",ai,self.LastKnownLocation,self.OnMoveCompleted,60.0f,self.UsePathfinding,true)
            }
            self.MoveRequests += 1
        }
    }

    [ue_function(BlueprintCallable)]
    def ForgetTarget() : void {
        ue_ai_move_cancel("Chase")
        let ai = ue_ai_self_controller()
        ue_ai_set_focus(ai,default<ActorRef>)
        let pawn = ue_ai_pawn(ai)
        if (ue_is_valid(pawn)) {
            let enemy = ue_ref(type<RogueAICharacterRef>,pawn.handle)
            enemy.ActionSystem.StopAction(ue_tag("Action.PrimaryAttack"))
            enemy.Target = default<ActorRef>
        }
        self.CurrentTarget = default<ActorRef>
    }

    def OnMoveCompleted(result:MoveResult) : void { self.MovesCompleted += 1 }

    def EndPlay(reason:int) : void { self.BrainEnabled = false }
}
