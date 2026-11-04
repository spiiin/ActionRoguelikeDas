options gen2
module rogue_projectile_blackhole public
require rogue_projectile public
require ue_radial_force public

// Adapted from ARogueProjectileBlackhole, course commit 992f860.
[ue_class(module_id="rogue", Blueprintable)]
class RogueProjectileBlackhole : RogueProjectile {
    @ue_component
    @Attach="SphereComponent"
    RadialForceComponent : RadialForceComponentRef

    state = ue_properties(BlueprintReadWrite) { var ConsumedActors : int = 0 }

    defaults = ue_defaults() {
        self.InitialSpeed = 500.0f
        self.CollisionRadius = 20.0f
        self.CollisionProfile = "BlackholeCore"
        self.InitialLifeSpan = 5.0f
        self.RadialForceComponent.ForceStrength = -800000.0f
        self.RadialForceComponent.Radius = 1200.0f
        self.RadialForceComponent.bAutoActivate = true
    }

    def override BeginPlay() : void {
        self.SphereComponent.SetGenerateOverlapEvents(true)
        verify(ue_radial_force_remove_channel(self.RadialForceComponent, ECollisionChannel.ECC_Pawn), "Cannot exclude Pawn force channel")
        Super.BeginPlay()
    }

    [ue_event(source=SphereComponent, name=OnComponentBeginOverlap)]
    def OnCoreOverlap(component : ObjectRef; other : ActorRef; otherComponent : ObjectRef;
        bodyIndex : int; fromSweep : bool; hit : CollisionHit) : void {
        if (!ue_is_valid(other) || !ue_is_valid(otherComponent) || !other.GetActorEnableCollision()) { return }
        let body = ue_ref(type<SceneComponentRef>, otherComponent.handle)
        if (!body.IsSimulatingPhysics(ue_name_value("None"))) { return }
        // Remove collision immediately; native lifespan dispatches foreign EndPlay outside this VM.
        other.SetActorEnableCollision(false)
        other.SetLifeSpan(0.001f)
        self.ConsumedActors += 1
    }
}

typedef RogueProjectileBlackholeRef = UEObjectRef("rogue.RogueProjectileBlackhole")
