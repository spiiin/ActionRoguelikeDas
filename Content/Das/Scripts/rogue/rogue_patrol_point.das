options gen2
module rogue_patrol_point public
require ue_navigation public
require ue_vector_math public
require math public


typedef RoguePatrolPointRef = UEObjectRef("rogue.RoguePatrolPoint")

// Adapted from RoguePatrolPoint in the pinned course source. Connections are
// rebuilt explicitly when the runtime navigation data is ready, outside actor tick.
[ue_class(module_id="rogue", Blueprintable)]
class RoguePatrolPoint : Actor {
    @ue_component
    SceneRoot : SceneComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Patrol") {
        var MaxPathLength : float = 1000.0f
    }

    state = ue_properties(BlueprintReadWrite, Category="Patrol") {
        var NearbyPatrolPoints : array<ActorRef>
        var ConnectionsReady : bool = false
    }

    def BeginPlay() : void { ue_self_actor().SetActorTickEnabled(false) }

    [ue_function(BlueprintCallable)]
    def RebuildConnections(points : array<ActorRef>) : bool {
        var previous := self.NearbyPatrolPoints
        var connected : array<ActorRef>
        let owner = ue_self_actor()
        let origin = owner.K2_GetActorLocation()
        let limit = double(max(self.MaxPathLength, 0.0f))
        for (point in points) {
            if (!ue_is_valid(point) || ue_same_object(owner, point)) { continue }
            let destination = point.K2_GetActorLocation()
            if (length_sq(destination-origin) > limit*limit) { continue }
            let distance = ue_navigation_distance(origin, destination)
            if (distance.Status == NavigationQueryStatus.Error || distance.Status == NavigationQueryStatus.Invalid) {
                // Preserve the previous graph until a complete rebuild is possible.
                self.ConnectionsReady = false
                return false
            }
            if (distance.Status == NavigationQueryStatus.Success && distance.Length <= limit) {
                push(connected, point)
            }
        }
        self.NearbyPatrolPoints := connected
        for (point in connected) {
            ue_ref(type<RoguePatrolPointRef>, point.handle).AddPatrolConnection(owner)
        }
        for (point in previous) {
            if (!ue_is_valid(point)) { continue }
            var retained = false
            for (next in connected) {
                if (ue_same_object(point, next)) { retained = true; break }
            }
            if (!retained) { ue_ref(type<RoguePatrolPointRef>, point.handle).RemovePatrolConnection(owner) }
        }
        self.ConnectionsReady = true
        return true
    }

    [ue_function(BlueprintCallable)]
    def AddPatrolConnection(point : ActorRef) : void {
        if (!ue_is_valid(point) || ue_same_object(point, ue_self_actor())) { return }
        for (existing in self.NearbyPatrolPoints) {
            if (ue_same_object(existing, point)) { return }
        }
        push(self.NearbyPatrolPoints, point)
    }

    [ue_function(BlueprintCallable)]
    def RemovePatrolConnection(point : ActorRef) : void {
        var connected := self.NearbyPatrolPoints
        for (i in range(length(connected))) {
            if (ue_same_object(connected[i], point)) { erase(connected, i); break }
        }
        self.NearbyPatrolPoints := connected
    }

    [ue_function(BlueprintPure)]
    def GetConnections() : array<ActorRef> {
        var connected : array<ActorRef>
        for (point in self.NearbyPatrolPoints) {
            if (ue_is_valid(point)) { push(connected, point) }
        }
        return <- connected
    }
}
