options gen2
module rogue_blackhole_attack_projectile public
require rogue_projectile_blackhole public
require rogue_presentation public

[ue_class(module_id="roguedemo", Blueprintable)]
class RogueBlackholeAttackProjectile : RogueProjectileBlackhole {
    @ue_component
    @Attach="SphereComponent"
    Visual : StaticMeshComponentRef

    defaults = ue_defaults() {
        self.Visual.StaticMesh = ue_asset_default("/Engine/BasicShapes/Sphere.Sphere")
        self.Visual.RelativeScale3D = ue_vector(0.4lf, 0.4lf, 0.4lf)
    }

    def override BeginPlay() : void {
        rogue_load_presentation() |> if_some() $(profile : RoguePresentationProfileRef) {
            if (ue_is_valid(profile.BlackholeEffect)) {
                ue_niagara_component_start(self.LoopedNiagaraComponent, profile.BlackholeEffect)
                self.Visual.SetHiddenInGame(true, false)
            }
            if (ue_is_valid(profile.BlackholeSound)) { ue_audio_component_play(self.LoopedAudioComponent, profile.BlackholeSound) }
        }
        self.Visual.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        Super.BeginPlay()
    }
}
