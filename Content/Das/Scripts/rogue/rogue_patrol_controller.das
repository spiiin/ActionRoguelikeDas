options gen2
module rogue_patrol_controller public
require rogue_ai_controller public
require rogue_patrol_point public
require ue_api_world public
require ue_api_math public
require math public

// The course's FindNextPatrolPoint behavior, layered over perception/combat.
[ue_class(module_id="rogue", Blueprintable)]
class RoguePatrolController : RogueAIController {
    patrolSettings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Patrol") {
        var PatrolEnabled : bool = true
        var PatrolPointClass : ActorClass
        var PatrolWait : float = 0.75f
        var PatrolRetryDelay : float = 1.0f
        var PatrolAcceptanceRadius : float = 40.0f
    }

    patrolState = ue_properties(BlueprintReadWrite) {
        var PatrolPoints : array<ActorRef>
        var CurrentPatrolPoint : RoguePatrolPointRef
        var PreviousPatrolPoint : RoguePatrolPointRef
        var PatrolDestination : RoguePatrolPointRef
        var PatrolGraphReady : bool = false
        var NextPatrolAt : double = 0.0lf
        var PatrolMovesStarted : int = 0
        var PatrolArrivals : int = 0
        var PatrolFailures : int = 0
    }

    defaults = ue_defaults() { self.UsePathfinding = true }

    def override Tick(delta : float) : void {
        let pawn = ue_ai_pawn(ue_ai_self_controller())
        if (!ue_is_valid(pawn)) { return }
        let enemy = ue_ref(type<RogueAICharacterRef>, pawn.handle)
        let interrupted = !self.PatrolEnabled || !self.BrainEnabled || enemy.Dead || enemy.Stunned || ue_is_valid(enemy.Target)
        // Cancel our request before the combat controller can replace it with Chase.
        if (interrupted) { ue_ai_move_cancel("Patrol") }
        Super.Tick(delta)
        if (interrupted || ue_is_valid(enemy.Target) || ue_world_seconds() < self.NextPatrolAt) { return }
        if (ue_ai_move_active("Patrol")) {
            if (!ue_is_valid(self.PatrolDestination)) {
                ue_ai_move_cancel("Patrol")
                self.PatrolDestination = default<RoguePatrolPointRef>
                self.PatrolGraphReady = false
                self.NextPatrolAt = ue_world_seconds() + double(max(self.PatrolRetryDelay, 0.1f))
            }
            return
        }
        if (!self.PatrolGraphReady && !self.RefreshPatrolGraph()) {
            self.NextPatrolAt = ue_world_seconds() + double(max(self.PatrolRetryDelay, 0.1f))
            return
        }
        if (!ue_is_valid(self.PatrolDestination)) { self.PatrolDestination = self.ChooseNextPoint() }
        if (!ue_is_valid(self.PatrolDestination)) {
            self.NextPatrolAt = ue_world_seconds() + double(max(self.PatrolRetryDelay, 0.1f))
            return
        }
        let destination = ue_ref(type<ActorRef>, self.PatrolDestination.handle)
        if (ue_ai_move_to_actor("Patrol", ue_ai_self_controller(), destination,
            self.OnPatrolMoveCompleted, max(self.PatrolAcceptanceRadius, 0.0f), true, false)) {
            self.PatrolMovesStarted += 1
        } else {
            self.NextPatrolAt = ue_world_seconds() + double(max(self.PatrolRetryDelay, 0.1f))
        }
    }

    [ue_function(BlueprintPure)]
    def IsPatrolling() : bool { return ue_ai_move_active("Patrol") }

    [ue_function(BlueprintCallable)]
    def RefreshPatrolGraph() : bool {
        self.PatrolGraphReady = false
        if (!ue_class_valid(self.PatrolPointClass)) { return false }
        var points : array<ActorRef>
        let actors <- ue_static(GameplayStatics.GetAllActorsOfClass, self.PatrolPointClass)
        for (actor in actors) { push(points, ue_ref(type<ActorRef>, actor.handle)) }
        self.PatrolPoints := points
        for (actor in points) {
            let point = ue_ref(type<RoguePatrolPointRef>, actor.handle)
            if (!point.RebuildConnections(points)) { return false }
        }
        self.PatrolGraphReady = true
        return true
    }

    [ue_function(BlueprintCallable)]
    def ChooseNextPoint() : RoguePatrolPointRef {
        if (!ue_is_valid(self.CurrentPatrolPoint)) {
            let pawn = ue_ai_pawn(ue_ai_self_controller())
            if (!ue_is_valid(pawn)) { return default<RoguePatrolPointRef> }
            let origin = ue_ref(type<ActorRef>, pawn.handle).K2_GetActorLocation()
            var nearest = -1.0lf
            for (point in self.PatrolPoints) {
                if (!ue_is_valid(point)) { continue }
                let distance = length_sq(point.K2_GetActorLocation()-origin)
                if (nearest < 0.0lf || distance < nearest) {
                    nearest = distance
                    self.CurrentPatrolPoint = ue_ref(type<RoguePatrolPointRef>, point.handle)
                }
            }
        }
        if (!ue_is_valid(self.CurrentPatrolPoint)) { return default<RoguePatrolPointRef> }
        var choices <- self.CurrentPatrolPoint.GetConnections()
        if (length(choices) > 1 && ue_is_valid(self.PreviousPatrolPoint)) {
            for (i in range(length(choices))) {
                if (ue_same_object(choices[i], self.PreviousPatrolPoint)) { erase(choices, i); break }
            }
        }
        if (empty(choices)) { return default<RoguePatrolPointRef> }
        let index = ue_static(KismetMathLibrary.RandomInteger, length(choices))
        return ue_ref(type<RoguePatrolPointRef>, choices[index].handle)
    }

    def OnPatrolMoveCompleted(result : MoveResult) : void {
        if (result.Code == MoveCode.Success && ue_is_valid(self.PatrolDestination)) {
            self.PreviousPatrolPoint = self.CurrentPatrolPoint
            self.CurrentPatrolPoint = self.PatrolDestination
            self.PatrolDestination = default<RoguePatrolPointRef>
            self.PatrolArrivals += 1
            self.NextPatrolAt = ue_world_seconds() + double(max(self.PatrolWait, 0.0f))
        } else {
            // Combat and stun preserve a live destination. Failed paths rebuild
            // the graph before another choice, rather than retrying an obsolete edge.
            if (result.Code != MoveCode.Aborted) {
                self.PatrolFailures += 1
                self.PatrolDestination = default<RoguePatrolPointRef>
                self.PatrolGraphReady = false
            }
            self.NextPatrolAt = ue_world_seconds() + double(max(self.PatrolRetryDelay, 0.1f))
        }
    }

    def override EndPlay(reason : int) : void {
        self.PatrolEnabled = false
        Super.EndPlay(reason)
    }
}

typedef RoguePatrolControllerRef = UEObjectRef("rogue.RoguePatrolController")
