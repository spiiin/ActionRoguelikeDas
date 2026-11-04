options gen2
module rogue_projectile_teleport public
require rogue_projectile public

// Adapted from ARogueProjectileTeleport, course commit 992f860.
[ue_class(module_id="rogue", Blueprintable)]
class RogueProjectileTeleport : RogueProjectile {
    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Teleport") {
        var DetonateDelay : float = 0.2f
        var TeleportSecondaryDelay : float = 0.2f
    }

    state = ue_properties(BlueprintReadWrite) {
        var TeleportAttempts : int = 0
        var TeleportSucceeded : bool = false
    }

    defaults = ue_defaults() { self.InitialSpeed = 6000.0f }

    def override BeginPlay() : void {
        Super.BeginPlay()
        ue_timer_start("Teleport", self.DetonateDelay, self.StartDelayedTeleport, false)
    }

    [ue_function(BlueprintEvent, Category="Projectile")]
    def override HandleImpact(other : ActorRef; hit : CollisionHit) : bool {
        if (self.HasImpacted) { return false }
        self.LastImpactActor = other
        self.LastImpactPoint = hit.ImpactPoint
        self.StartDelayedTeleport()
        return true
    }

    [ue_function(BlueprintCallable)]
    def StartDelayedTeleport() : void {
        if (self.HasImpacted) { return }
        self.HasImpacted = true
        self.ImpactCount += 1
        ue_timer_cancel("Teleport")
        self.PlayExplodeEffects()
        ue_projectile_movement_stop(self.ProjectileMovementComponent)
        ue_ref(type<ActorComponentRef>, self.LoopedNiagaraComponent.handle).Deactivate()
        self.LoopedAudioComponent.Stop()
        self.SetActorHiddenInGame(true)
        self.SetActorEnableCollision(false)
        ue_timer_start("Teleport", self.TeleportSecondaryDelay, self.HandleTeleportation, false)
    }

    [ue_function]
    def HandleTeleportation() : void {
        if (ue_is_valid(self.Instigator)) {
            let pawn = ue_ref(type<ActorRef>, self.Instigator.handle)
            self.TeleportAttempts += 1
            self.TeleportSucceeded = pawn.K2_TeleportTo(self.K2_GetActorLocation(), pawn.K2_GetActorRotation())
        }
        ue_actor_destroy_self_next_tick()
    }

    // The owner session cancels timers; only mark gameplay state as finished here.
    def EndPlay(reason : int) : void { self.HasImpacted = true }
}

typedef RogueProjectileTeleportRef = UEObjectRef("rogue.RogueProjectileTeleport")
