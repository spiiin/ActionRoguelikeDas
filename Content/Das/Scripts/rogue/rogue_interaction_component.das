options gen2
module rogue_interaction_component public
require ue_native_gameplay public
require rogue_interaction
require math
require ue_vector_math public

// Adapted from Tom Looman's RogueInteractionComponent, commit 992f860.
// Publication permission and redistribution license are pending.
[ue_class(module_id="rogue", Blueprintable)]
class RogueInteractionComponent : ActorComponent {

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Interaction") {
        var InteractionRadius : float = 800.0f
        var DistanceToWeightScale : float = 2.0f
        var DirectionWeightScale : float = 1.0f
    }

    state = ue_properties(BlueprintReadWrite) {
        var SelectedActor : ActorRef
        var CandidateCount : int = 0
        var HighestWeight : float = 0.0f
    }

    def Tick(delta : float) : void { self.UpdateSelection() }

    [ue_function(BlueprintCallable)]
    def UpdateSelection() : void {
        self.SelectedActor = default<ActorRef>
        self.CandidateCount = 0
        self.HighestWeight = 0.0f
        let owner = ue_component_owner(ue_self_object())
        if (!ue_object_valid(owner) || !ue_object_is_a(owner, "/Script/Engine.PlayerController") || self.InteractionRadius <= 0.0f) { return }
        let player = ue_ref(type<PlayerControllerRef>, owner)
        let pawn = player.K2_GetPawn()
        if (!ue_object_valid(pawn.handle)) { return }
        let center = ue_ref(type<ActorRef>, pawn.handle).K2_GetActorLocation()
        var camera = UE_VECTOR_ZERO
        var view = UE_ROTATOR_ZERO
        player.GetPlayerViewPoint(camera, view)
        let forward = ue_rotate_vector(player.GetControlRotation(), UE_VECTOR_FORWARD)
        let radius = double(self.InteractionRadius)
        let radiusSquared = radius * radius
        let overlaps <- ue_sphere_overlap(center, double(self.InteractionRadius), TraceChannel.GameTrace1)
        for (hit in overlaps) {
            let candidate = ue_overlap_actor(hit)
            if (!rogue_can_interact(candidate)) { continue }
            self.CandidateCount += 1
            var origin = UE_VECTOR_ZERO
            var extent = UE_VECTOR_ZERO
            candidate.GetActorBounds(true, origin, extent, false)
            let offset = origin - center
            let direction = origin - camera
            let directionSquared = length_sq(direction)
            var facingDot = 0.0lf
            if (directionSquared > 1.0e-8lf) {
                facingDot = dot(direction, forward) / sqrt(directionSquared)
            }
            let normalizedDistance = 1.0lf - length_sq(offset) / radiusSquared
            let normalizedDirection = facingDot * 0.5lf + 0.5lf
            let weight = float(normalizedDirection) * self.DirectionWeightScale + float(normalizedDistance) * self.DistanceToWeightScale
            if (weight > self.HighestWeight) {
                self.SelectedActor = candidate
                self.HighestWeight = weight
            }
        }
    }

    [ue_function(BlueprintCallable)]
    def Interact() : bool {
        // Requery at the input edge, so a moved or destroyed target is never reused.
        self.UpdateSelection()
        return rogue_interact(self.SelectedActor)
    }
}

typedef RogueInteractionComponentRef = UEObjectRef("rogue.RogueInteractionComponent")
