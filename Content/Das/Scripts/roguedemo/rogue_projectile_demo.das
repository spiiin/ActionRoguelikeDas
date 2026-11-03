options gen2
require rogue_projectile

// Engine mesh only: visible test projectile, no course assets.
[ue_class(module_id="roguedemo", Blueprintable)]
class RogueProjectileDemo : RogueProjectile {
    @ue_component
    @Attach = "SphereComponent"
    Visual : StaticMeshComponentRef

    defaults = ue_defaults() {
        self.ExplosionSound = ue_asset_default("/Engine/EngineSounds/1kSineTonePing.1kSineTonePing")
        self.ExplosionEffect = ue_asset_default("/Niagara/DefaultAssets/Templates/Systems/RadialBurst.RadialBurst")
        self.Visual.StaticMesh = ue_asset_default("/Engine/BasicShapes/Sphere.Sphere")
        self.Visual.RelativeScale3D = ue_vector(0.25lf, 0.25lf, 0.25lf)
    }

    def override BeginPlay() : void {
        self.Visual.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        Super.BeginPlay()
    }
}
