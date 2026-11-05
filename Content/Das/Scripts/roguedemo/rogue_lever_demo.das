options gen2
module rogue_lever_demo public
require rogue_lever public

// Portable stand-in for the optional course switch meshes. The original has no animation.
[ue_class(module_id="roguedemo", Blueprintable)]
class RogueLeverDemo : RogueLever {
    defaults = ue_defaults() {
        self.SwitchBaseMeshComp.StaticMesh = ue_asset_default("/Engine/BasicShapes/Cube.Cube")
        self.SwitchBaseMeshComp.RelativeScale3D = ue_vector(0.6lf, 0.6lf, 0.2lf)
        self.HandleMeshComp.StaticMesh = ue_asset_default("/Engine/BasicShapes/Cylinder.Cylinder")
        self.HandleMeshComp.RelativeLocation = ue_vector(0.0lf, 0.0lf, 130.0lf)
        self.HandleMeshComp.RelativeScale3D = ue_vector(0.2lf, 0.2lf, 2.0lf)
    }
}
