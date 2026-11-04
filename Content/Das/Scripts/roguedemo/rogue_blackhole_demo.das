options gen2
module rogue_blackhole_demo public
require rogue_projectile_blackhole public

typedef BlackholeMaterialRef = UENativeObjectRef("/Script/Engine.MaterialInterface")

// Stationary, visible presentation for the physics arena; the course projectile still moves.
[ue_class(module_id="roguedemo", Blueprintable)]
class RogueBlackholeDemo : RogueProjectileBlackhole {
    @ue_component
    @Attach="SphereComponent"
    CoreVisual : StaticMeshComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite) { var CoreMaterial : BlackholeMaterialRef }

    defaults = ue_defaults() {
        self.InitialSpeed = 0.0f
        self.CoreVisual.StaticMesh = ue_asset_default("/Engine/BasicShapes/Sphere.Sphere")
        self.CoreVisual.RelativeScale3D = ue_vector(0.35lf,0.35lf,0.35lf)
        self.CoreMaterial = ue_asset_default("/Game/DasRogue/Materials/M_TargetHealth.M_TargetHealth")
    }

    def override BeginPlay() : void {
        Super.BeginPlay()
        self.CoreVisual.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        self.CoreVisual.SetMaterial(0, self.CoreMaterial)
        self.CoreVisual.SetVectorParameterValueOnMaterials(ue_name_value("Color"), ue_vector(0.025lf,0.0lf,0.08lf))
    }
}
