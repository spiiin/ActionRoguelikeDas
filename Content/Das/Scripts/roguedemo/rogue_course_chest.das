options gen2
module rogue_course_chest public
require rogue_item_chest public
require ue_effects public
require ue_projectile_components public
require ue_vector_math public

// Original chest mesh/pivot and treasure are supplied by the local course-map importer.
[ue_class(module_id="roguedemo", Blueprintable)]
class RogueCourseChest : RogueItemChest {
    @ue_component
    @Attach="BaseMeshComponent"
    TreasurePile : StaticMeshComponentRef

    @ue_component
    @Attach="BaseMeshComponent"
    TreasureBurst : NiagaraComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite) {
        var TreasureSound : SoundBaseRef
    }

    defaults = ue_defaults() { self.TreasureBurst.bAutoActivate = false }

    def override BeginPlay() : void {
        self.TreasurePile.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        Super.BeginPlay()
    }

    [ue_function(BlueprintEvent, Category="Interaction")]
    def override ChestInteractionStarted() : void {
        if (ue_is_valid(self.TreasureSound)) {
            ue_effect_burst(self.TreasureSound, default<NiagaraSystemRef>,
                ue_transform(self.K2_GetActorLocation(), UE_ROTATOR_ZERO, UE_VECTOR_ONE))
        }
    }

    [ue_function(BlueprintEvent)]
    def override ChestAnimationComplete() : void {
        ue_ref(type<ActorComponentRef>, self.TreasureBurst.handle).Activate(false)
    }
}
