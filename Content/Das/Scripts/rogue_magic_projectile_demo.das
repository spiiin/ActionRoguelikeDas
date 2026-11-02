options gen2
require rogue_magic_projectile

[ue_class(module_id="roguedemo", Blueprintable)]
class RogueMagicProjectileDemo : RogueMagicProjectile {
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
