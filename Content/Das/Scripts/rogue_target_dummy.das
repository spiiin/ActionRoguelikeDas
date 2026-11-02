options gen2
require rogue_attribute_refs

[ue_class(module_id="roguedemo", Blueprintable)]
class RogueTargetDummy : Actor {
    @ue_component
    @RootComponent
    Root : SceneComponentRef
    @ue_component
    @Attach = "Root"
    Visual : StaticMeshComponentRef
    @ue_component
    @Attach = "Root"
    Label : TextRenderComponentRef
    @ue_component
    Attributes : RogueAttributeComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Target") {
        var DeathDelay : float = 0.4f
        var TargetMaterial : Native_MaterialInterfaceRef_d64f3063
    }

    state = ue_properties(BlueprintReadWrite) {
        var Hits : int = 0
        var Dead : bool = false
    }

    defaults = ue_defaults() {
        self.TargetMaterial = ue_asset_default("/Game/DasRogue/Materials/M_TargetHealth.M_TargetHealth")
        self.Visual.StaticMesh = ue_asset_default("/Engine/BasicShapes/Cube.Cube")
        self.Visual.RelativeScale3D = ue_vector(0.7lf, 0.7lf, 1.0lf)
        self.Label.RelativeLocation = ue_vector(0.0lf, 0.0lf, 80.0lf)
        self.Label.WorldSize = 22.0f
    }

    def BeginPlay() : void {
        self.Visual.SetMaterial(0, self.TargetMaterial)
        self.Visual.SetCollisionProfileName(ue_name_value("BlockAll"), true)
        self.Attributes.OnHealthChanged.AddUFunction(ue_self_object(), "OnHealthChanged")
        self.UpdateDisplay()
        ue_self_actor().SetActorTickEnabled(false)
    }

    def UpdateDisplay() : void {
        self.Label.K2_SetText(ue_text_invariant("HP: {int(self.Attributes.Health)} / {int(self.Attributes.HealthMax)}"))
        let ratio = self.Attributes.HealthMax > 0.0f ? self.Attributes.Health / self.Attributes.HealthMax : 0.0f
        self.Visual.SetVectorParameterValueOnMaterials(ue_name_value("Color"), ue_vector(double(1.0f - ratio), double(ratio), 0.05lf))
    }

    [ue_function(BlueprintCallable)]
    def OnHealthChanged(instigator : ActorRef; newHealth : float; delta : float) : void {
        if (delta < 0.0f) { self.Hits += 1 }
        self.UpdateDisplay()
        if (newHealth <= 0.0f && !self.Dead) {
            self.Dead = true
            ue_timer_start("death", self.DeathDelay, "Die", false)
        }
    }

    [ue_function(BlueprintCallable)]
    def Die() : void { ue_actor_destroy_self() }
}
