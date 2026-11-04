options gen2
require rogue_magic_projectile
require rogue_presentation public

[ue_class(module_id="roguedemo", Blueprintable)]
class RogueMagicProjectileDemo : RogueMagicProjectile {
    @ue_component
    @Attach = "SphereComponent"
    Visual : StaticMeshComponentRef

    defaults = ue_defaults() {
        self.EffectOnHit = ue_class_default("/Game/DasRogue/Actions/BP_RogueActionEffectBurning.BP_RogueActionEffectBurning_C")
        self.ExplosionSound = ue_asset_default("/Engine/EngineSounds/1kSineTonePing.1kSineTonePing")
        self.ExplosionEffect = ue_asset_default("/Niagara/DefaultAssets/Templates/Systems/RadialBurst.RadialBurst")
        self.Visual.StaticMesh = ue_asset_default("/Engine/BasicShapes/Sphere.Sphere")
        self.Visual.RelativeScale3D = ue_vector(0.25lf, 0.25lf, 0.25lf)
    }

    def override BeginPlay() : void {
        rogue_load_presentation() |> if_some() $(presentation : RoguePresentationProfileRef) {
            if (ue_is_valid(presentation.ProjectileEffect)) {
                ue_niagara_component_start(self.LoopedNiagaraComponent, presentation.ProjectileEffect)
                self.Visual.SetHiddenInGame(true, false)
            }
            if (ue_is_valid(presentation.ProjectileSound)) {
                ue_audio_component_play(self.LoopedAudioComponent, presentation.ProjectileSound)
            }
            if (ue_is_valid(presentation.ImpactEffect)) { self.ExplosionEffect = presentation.ImpactEffect }
            if (ue_is_valid(presentation.ImpactSound)) { self.ExplosionSound = presentation.ImpactSound }
        }
        self.Visual.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        Super.BeginPlay()
    }
}
