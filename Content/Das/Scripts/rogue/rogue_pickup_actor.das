options gen2
module rogue_pickup_actor public
require rogue_interaction public
require ue_projectile_components public
require ue_api_world public
require ue_vector_math public
require math public

// Original overlap pickup, with optional interaction and respawn for the demo.
[ue_class(module_id="rogue", Blueprintable),
 ue_implements(interface="/Game/DasRogue/Types/RogueInteractionInterface.RogueInteractionInterface_C")]
class RoguePickupActor : Actor {
    @ue_component
    @RootComponent
    OverlapComponent : SphereComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Pickup") {
        var PickupRadius : float = 128.0f
        var RequireInteraction : bool = false
        var InteractionDistance : float = 250.0f
        // Zero preserves the original one-shot pickup behavior.
        var RespawnDelay : float = 0.0f
    }

    state = ue_properties(BlueprintReadWrite) {
        var Available : bool = true
        var Collections : int = 0
        var Respawns : int = 0
    }

    def BeginPlay() : void {
        self.OverlapComponent.SetSphereRadius(max(self.PickupRadius, 0.0f), false)
        self.OverlapComponent.SetCollisionEnabled(ECollisionEnabled.QueryOnly)
        self.OverlapComponent.SetCollisionResponseToAllChannels(ECollisionResponse.ECR_Ignore)
        if (self.RequireInteraction) {
            self.OverlapComponent.SetCollisionResponseToChannel(ECollisionChannel.ECC_GameTraceChannel1, ECollisionResponse.ECR_Block)
        } else {
            self.OverlapComponent.SetCollisionResponseToChannel(ECollisionChannel.ECC_Pawn, ECollisionResponse.ECR_Overlap)
        }
        self.OverlapComponent.SetGenerateOverlapEvents(!self.RequireInteraction)
        ue_self_actor().SetActorTickEnabled(false)
    }

    [ue_event(source=OverlapComponent, name=OnComponentBeginOverlap)]
    def OnActorOverlapped(component : ObjectRef; other : ActorRef; otherComponent : ObjectRef;
        bodyIndex : int; fromSweep : bool; hit : CollisionHit) : void {
        if (!self.RequireInteraction) { self.TryCollect(other) }
    }

    [ue_function(BlueprintCallable)]
    def Interact() : void {
        if (!self.RequireInteraction || !self.Available) { return }
        // The course interface has no interactor argument; this demo uses local player 0.
        let player = ue_static(GameplayStatics.GetPlayerController, 0)
        if (!ue_is_valid(player)) { return }
        let pawn = ue_ref(type<PlayerControllerRef>, player.handle).K2_GetPawn()
        if (!ue_is_valid(pawn)) { return }
        let target = ue_ref(type<ActorRef>, pawn.handle)
        let distance = double(max(self.InteractionDistance, 0.0f))
        if (length_sq(target.K2_GetActorLocation()-ue_self_actor().K2_GetActorLocation()) <= distance*distance) {
            self.TryCollect(target)
        }
    }

    [ue_function(BlueprintCallable)]
    def TryCollect(target : ActorRef) : bool {
        if (!self.Available || !ue_is_valid(target)) { return false }
        // Reserve before health events can re-enter collection.
        self.Available = false
        if (!self.ApplyPickup(target)) {
            self.Available = true
            return false
        }
        self.Collections += 1
        let actor = ue_self_actor()
        actor.SetActorHiddenInGame(true)
        actor.SetActorEnableCollision(false)
        if (is_finite(self.RespawnDelay) && self.RespawnDelay > 0.0f) {
            ue_timer_start("respawn", self.RespawnDelay, self.Respawn, false)
        } else {
            // Deliver queued health notifications while their source is still valid.
            ue_actor_destroy_self_next_tick()
        }
        return true
    }

    [ue_function(BlueprintEvent)]
    def ApplyPickup(target : ActorRef) : bool { return false }

    def Respawn() : void {
        self.Respawns += 1
        self.Available = true
        let actor = ue_self_actor()
        actor.SetActorHiddenInGame(false)
        actor.SetActorEnableCollision(true)
    }

    def EndPlay(reason : int) : void { self.Available = false }
}

typedef RoguePickupActorRef = UEObjectRef("rogue.RoguePickupActor")
