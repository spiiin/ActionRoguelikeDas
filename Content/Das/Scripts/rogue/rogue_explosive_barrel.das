options gen2
module rogue_explosive_barrel public
require ue_radial_force public
require ue_projectile_components public
require ue_vector_math public
require ue_effects public
require math

// Adapted from ARogueExplosiveBarrel, course commit 992f860.
// Native damage notifications start the fuse; the blast applies impulse, not damage.
[ue_class(module_id="rogue", Blueprintable)]
class RogueExplosiveBarrel : Actor {
    @ue_component
    @RootComponent
    MeshComponent : StaticMeshComponentRef

    @ue_component
    @Attach="MeshComponent"
    RadialForceComponent : RadialForceComponentRef

    @ue_component
    @Attach="MeshComponent"
    BurningEffectComponent : NiagaraComponentRef

    @ue_component
    @Attach="MeshComponent"
    BurningAudioComponent : AudioComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Explosive Barrel") {
        var ExplosionDelay : float = 3.0f
        var ExplosionEffect : NiagaraSystemRef
        var ExplosionSound : SoundBaseRef
        var BurningEffect : NiagaraSystemRef
        var BurningSound : SoundBaseRef
    }

    state = ue_properties(BlueprintReadWrite) {
        var Burning : bool = false
        var Exploded : bool = false
        var FuseStarts : int = 0
        var Explosions : int = 0
    }

    defaults = ue_defaults() {
        self.MeshComponent.StaticMesh = ue_asset_default("/Engine/BasicShapes/Cylinder.Cylinder")
        self.MeshComponent.bCanEverAffectNavigation = false
        self.RadialForceComponent.ImpulseStrength = 150000.0f
        self.RadialForceComponent.Radius = 750.0f
        self.RadialForceComponent.bAutoActivate = false
        self.RadialForceComponent.bIgnoreOwningActor = true
        self.BurningEffectComponent.bAutoActivate = false
        self.BurningAudioComponent.bAutoActivate = false
    }

    def BeginPlay() : void {
        self.MeshComponent.SetCollisionProfileName(ue_name_value("PhysicsActor"), true)
        self.MeshComponent.SetSimulatePhysics(true)
        self.SetActorTickEnabled(false)
    }

    [ue_event(source=self, name=OnTakeAnyDamage)]
    def OnDamage(damaged : ActorRef; amount : float; kind : ObjectRef; instigator : ObjectRef; source : ActorRef) : void {
        if (self.Burning || self.Exploded || !is_finite(self.ExplosionDelay) || self.ExplosionDelay <= 0.0f) { return }
        self.Burning = true
        self.FuseStarts += 1
        if (ue_is_valid(self.BurningEffect)) { ue_niagara_component_start(self.BurningEffectComponent, self.BurningEffect) }
        if (ue_is_valid(self.BurningSound)) { ue_audio_component_play(self.BurningAudioComponent, self.BurningSound) }
        ue_timer_start("Explosion", self.ExplosionDelay, self.Explode, false)
    }

    [ue_function(BlueprintCallable)]
    def Explode() : void {
        if (self.Exploded) { return }
        self.Exploded = true
        self.Explosions += 1
        ue_timer_cancel("Explosion")
        self.StopBurning()
        self.RadialForceComponent.FireImpulse()
        self.MeshComponent.AddImpulse(UE_VECTOR_UP * 1000.0lf, ue_name_value("None"), true)
        self.MeshComponent.AddAngularImpulseInDegrees(UE_VECTOR_RIGHT * 1000.0lf, ue_name_value("None"), true)
        ue_effect_burst(self.ExplosionSound, self.ExplosionEffect,
            ue_transform(self.K2_GetActorLocation(), self.K2_GetActorRotation(), UE_VECTOR_ONE))
    }

    def StopBurning() : void {
        self.Burning = false
        ue_ref(type<ActorComponentRef>, self.BurningEffectComponent.handle).Deactivate()
        self.BurningAudioComponent.Stop()
    }

    // Unreal tears down owned components; managed owner teardown cancels the fuse.
    def EndPlay(reason : int) : void { self.Burning = false }
}

typedef RogueExplosiveBarrelRef = UEObjectRef("rogue.RogueExplosiveBarrel")
