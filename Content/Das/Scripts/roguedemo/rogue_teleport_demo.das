options gen2
module rogue_teleport_demo public
require rogue_projectile_teleport public
require rogue_presentation public

[ue_class(module_id="roguedemo", Blueprintable)]
class RogueTeleportDemo : RogueProjectileTeleport {
    @ue_component
    @Attach="SphereComponent"
    Visual : StaticMeshComponentRef

    defaults = ue_defaults() {
        self.Visual.StaticMesh = ue_asset_default("/Engine/BasicShapes/Sphere.Sphere")
        self.Visual.RelativeScale3D = ue_vector(0.25lf, 0.25lf, 0.25lf)
        self.ExplosionEffect = ue_asset_default("/Niagara/DefaultAssets/Templates/Systems/RadialBurst.RadialBurst")
    }

    def override BeginPlay() : void {
        rogue_load_presentation() |> if_some() $(profile : RoguePresentationProfileRef) {
            if (ue_is_valid(profile.ProjectileEffect)) {
                ue_niagara_component_start(self.LoopedNiagaraComponent, profile.ProjectileEffect)
                self.Visual.SetHiddenInGame(true, false)
            }
            if (ue_is_valid(profile.ProjectileSound)) { ue_audio_component_play(self.LoopedAudioComponent, profile.ProjectileSound) }
            if (ue_is_valid(profile.TeleportImpactEffect)) { self.ExplosionEffect = profile.TeleportImpactEffect }
            self.ExplosionSound = profile.TeleportImpactSound
        }
        self.Visual.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        Super.BeginPlay()
    }
}
