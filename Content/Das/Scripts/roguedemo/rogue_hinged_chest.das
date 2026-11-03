options gen2
require ue_vector_math public
require rogue_item_chest

let CHEST_BODY_SCALE = ue_vector(2.0lf, 1.3lf, 1.0lf)
let CHEST_LID_HINGE = ue_vector(-51.25lf, 0.0lf, 50.0lf)
let CHEST_LID_CENTER_OFFSET = ue_vector(51.25lf, 0.0lf, 7.5lf)
let CHEST_LID_VISUAL_SCALE = ue_vector(1.025lf, 1.04lf, 0.15lf)

// Engine cube has a centre pivot. Keep the animated component at the rear
// edge and offset the visible cover so it rotates around a real hinge.
[ue_class(module_id="roguedemo", Blueprintable)]
class RogueInteractiveChestHinged : RogueItemChest {
    @ue_component
    @Attach = "LidMeshComponent"
    LidVisual : StaticMeshComponentRef

    defaults = ue_defaults() {
        self.BaseMeshComponent.StaticMesh = ue_asset_default("/Engine/BasicShapes/Cube.Cube")
        self.BaseMeshComponent.RelativeScale3D = CHEST_BODY_SCALE
        self.LidMeshComponent.RelativeLocation = CHEST_LID_HINGE
        self.LidMeshComponent.RelativeScale3D = UE_VECTOR_ONE
        self.LidVisual.StaticMesh = ue_asset_default("/Engine/BasicShapes/Cube.Cube")
        self.LidVisual.RelativeLocation = CHEST_LID_CENTER_OFFSET
        self.LidVisual.RelativeScale3D = CHEST_LID_VISUAL_SCALE
    }

    def override BeginPlay() : void {
        self.LidVisual.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        Super.BeginPlay()
    }
}
