options gen2
module rogue_health_pickup public
require rogue_pickup_actor public
require rogue_attribute_component public
require ue_effects public

typedef PickupMaterialRef = UENativeObjectRef("/Script/Engine.MaterialInterface")

// Health slice of ARogueHealthPickup from the pinned course source.
[ue_class(module_id="rogue", Blueprintable)]
class RogueHealthPickup : RoguePickupActor {
    @ue_component
    @Attach = "OverlapComponent"
    PickupMeshComponent : StaticMeshComponentRef

    healthSettings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Pickup") {
        var HealingAmount : float = 50.0f
        var PickupSound : SoundBaseRef
        var PickupMaterial : PickupMaterialRef
    }

    defaults = ue_defaults() {
        self.PickupMeshComponent.StaticMesh = ue_asset_default("/Engine/BasicShapes/Sphere.Sphere")
        self.PickupMeshComponent.RelativeScale3D = ue_vector(0.45lf, 0.45lf, 0.45lf)
        self.PickupMaterial = ue_asset_default("/Game/DasRogue/Materials/M_TargetHealth.M_TargetHealth")
    }

    def override BeginPlay() : void {
        Super.BeginPlay()
        self.PickupMeshComponent.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        if (ue_is_valid(self.PickupMaterial)) {
            self.PickupMeshComponent.SetMaterial(0, self.PickupMaterial)
            self.PickupMeshComponent.SetVectorParameterValueOnMaterials(ue_name_value("Color"), ue_vector(0.05lf, 1.0lf, 0.1lf))
        }
    }

    [ue_function(BlueprintEvent)]
    def override ApplyPickup(target : ActorRef) : bool {
        if (!is_finite(self.HealingAmount) || self.HealingAmount <= 0.0f) { return false }
        let attributes = ue_component_find(type<RogueAttributeComponentRef>, target)
        if (!ue_is_valid(attributes) || !attributes.IsAlive() || attributes.Health >= attributes.HealthMax) { return false }
        if (!attributes.ApplyHealthChange(ue_self_actor(), self.HealingAmount)) { return false }
        if (ue_is_valid(self.PickupSound)) {
            ue_effect_burst(self.PickupSound, default<NiagaraSystemRef>,
                ue_transform(ue_self_actor().K2_GetActorLocation(), UE_ROTATOR_ZERO, UE_VECTOR_ONE))
        }
        return true
    }
}

typedef RogueHealthPickupRef = UEObjectRef("rogue.RogueHealthPickup")
