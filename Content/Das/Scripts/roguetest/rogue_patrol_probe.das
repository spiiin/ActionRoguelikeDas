options gen2
module rogue_patrol_probe public
require rogue_action_probe public
require rogue_patrol_controller public

[ue_class(module_id="roguetest", Blueprintable)]
class RoguePatrolProbe : RogueActionProbe {
    [ue_function(BlueprintCallable)]
    def PausePatrol(actor : ActorRef) : void {
        let controller = ue_ref(type<RoguePatrolControllerRef>, actor.handle)
        controller.PatrolEnabled = false
        controller.BrainEnabled = false
        controller.ForgetTarget()
    }

    [ue_function(BlueprintCallable)]
    def ConfigureRoute(actor : ActorRef; start : ActorRef; previous : ActorRef; destination : ActorRef) : void {
        let controller = ue_ref(type<RoguePatrolControllerRef>, actor.handle)
        controller.CurrentPatrolPoint = ue_ref(type<RoguePatrolPointRef>, start.handle)
        controller.PreviousPatrolPoint = ue_ref(type<RoguePatrolPointRef>, previous.handle)
        controller.PatrolDestination = ue_ref(type<RoguePatrolPointRef>, destination.handle)
        controller.NextPatrolAt = 0.0lf
    }

    [ue_function(BlueprintCallable)]
    def StartRoute(actor : ActorRef; start : ActorRef; previous : ActorRef; destination : ActorRef) : void {
        let controller = ue_ref(type<RoguePatrolControllerRef>, actor.handle)
        controller.CurrentPatrolPoint = ue_ref(type<RoguePatrolPointRef>, start.handle)
        controller.PreviousPatrolPoint = ue_ref(type<RoguePatrolPointRef>, previous.handle)
        controller.PatrolDestination = ue_ref(type<RoguePatrolPointRef>, destination.handle)
        controller.NextPatrolAt = 0.0lf
        controller.PatrolEnabled = true
        controller.BrainEnabled = true
    }

    [ue_function(BlueprintCallable)]
    def HasFullRoute(start : UEVector; finish : UEVector) : bool {
        let path = ue_navigation_path(start, finish)
        return ue_is_valid(path) && path.IsValid() && !path.IsPartial()
    }

    [ue_function(BlueprintCallable)]
    def QueryDistance(start : UEVector; finish : UEVector) : double {
        let distance = ue_navigation_distance(start, finish)
        return distance.Status == NavigationQueryStatus.Success ? distance.Length : -1.0lf
    }

    [ue_function(BlueprintCallable)]
    def SetPathLimit(actor : ActorRef; limit : float) : void {
        ue_ref(type<RoguePatrolPointRef>, actor.handle).MaxPathLength = limit
    }
}
