options gen2
module rogue_projectile public
require ue_vector_math public
require ue_projectile_components public

// Adapted from Tom Looman's ARogueProjectile, commit 992f860.
// Publication permission and redistribution license are pending.
[ue_class(module_id="rogue", Blueprintable),
 ue_implements(interface="/Game/DasRogue/Types/RogueImpactHandler.RogueImpactHandler_C")]
class RogueProjectile : Actor {
    @ue_component
    @RootComponent
    SphereComponent : SphereComponentRef
    @ue_component
    ProjectileMovementComponent : ProjectileMovementComponentRef
    @ue_component
    @Attach = "SphereComponent"
    LoopedNiagaraComponent : NiagaraComponentRef
    @ue_component
    @Attach = "SphereComponent"
    LoopedAudioComponent : AudioComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Projectile") {
        var InitialSpeed : float = 2000.0f
        var GravityScale : float = 0.0f
        var CollisionRadius : float = 16.0f
        var ExplosionEffect : NiagaraSystemRef
        var ExplosionSound : SoundBaseRef
    }

    state = ue_properties(BlueprintReadWrite) {
        var HasImpacted : bool = false
        var ImpactCount : int = 0
    }

    defaults = ue_defaults() { self.InitialLifeSpan = 30.0f }

    def BeginPlay() : void {
        self.SphereComponent.SetSphereRadius(self.CollisionRadius, false)
        self.SphereComponent.SetCollisionProfileName(ue_name_value("Projectile"), true)
        let actor = ue_ref(type<ActorRef>, ue_self_object())
        let instigator = self.Instigator
        if (ue_object_valid(instigator.handle)) {
            self.SphereComponent.IgnoreActorWhenMoving(ue_ref(type<ActorRef>, instigator.handle), true)
        }
        ue_projectile_movement_launch(self.ProjectileMovementComponent,
            ue_ref(type<SceneComponentRef>, self.SphereComponent.handle),
            UE_VECTOR_FORWARD * double(self.InitialSpeed), self.GravityScale)
        actor.SetActorTickEnabled(false)
    }

    [ue_event(source="SphereComponent", name="OnComponentHit")]
    def OnActorHit(component : ObjectRef; other : ActorRef; otherComponent : ObjectRef; impulse : UEVector; hit : CollisionHit) : void {
        if (self.HasImpacted) { return }
        self.HasImpacted = true
        self.ImpactCount += 1
        let impact = ue_begin_interface_call(ue_self_object(),
            "/Game/DasRogue/Types/RogueImpactHandler.RogueImpactHandler_C", "ApplyProjectileDamage")
        ue_arg_object(impact, "other", other.handle)
        ue_arg_collision_hit(impact, "hit", hit)
        ue_invoke_call(impact)
        ue_release_call(impact)
        self.PlayExplodeEffects()
        // OnTakeAnyDamage is queued while this managed callback runs. Keep the
        // damage causer alive until its notifications have been delivered.
        ue_actor_destroy_self_next_tick()
    }

    // Reflected event dispatch preserves overrides on derived projectile classes.
    [ue_function(BlueprintEvent, Category="Projectile")]
    def ApplyProjectileDamage(other : ActorRef; hit : CollisionHit) : bool { return false }

    def PlayExplodeEffects() : void {
        let actor = ue_ref(type<ActorRef>, ue_self_object())
        let pose = ue_transform(actor.K2_GetActorLocation(), UE_ROTATOR_ZERO, UE_VECTOR_ONE)
        ue_effect_burst(self.ExplosionSound, self.ExplosionEffect, pose)
    }
}
