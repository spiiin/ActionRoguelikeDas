options gen2
module rogue_burning_target public
require rogue_attribute_component public
require rogue_action_system_component public
require ue_vector_math public

// Isolated damage receiver: no AI, Overwhelm, respawn or destruction timer.
[ue_class(module_id="roguetest", Blueprintable)]
class RogueBurningTarget : Actor {
    @ue_component
    @RootComponent
    Visual : StaticMeshComponentRef

    @ue_component
    Attributes : RogueAttributeComponentRef

    @ue_component
    ActionSystem : RogueActionSystemComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite) {
        var AttributeSetClass : ObjectClass
    }

    state = ue_properties(BlueprintReadWrite) {
        var DamageEvents : int = 0
        var LastDamage : float = 0.0f
        var LastSource : ActorRef
        var LastController : ObjectRef
        var Dead : bool = false
    }

    defaults = ue_defaults() {
        self.AttributeSetClass = ue_class_default("/Game/DasRogue/Attributes/BP_RoguePlayerAttributeSet.BP_RoguePlayerAttributeSet_C")
        self.Visual.StaticMesh = ue_asset_default("/Engine/BasicShapes/Cube.Cube")
        self.Visual.RelativeScale3D = ue_vector(0.7lf,0.7lf,1.0lf)
    }

    def BeginPlay() : void {
        self.ActionSystem.ConfigureAttributeSet(self.AttributeSetClass)
        self.Visual.SetCollisionProfileName(ue_name_value("BlockAll"), true)
        self.SetActorTickEnabled(false)
    }

    def BindEvents() : void { self.Attributes.OnHealthChanged += self.OnHealthChanged }

    def OnHealthChanged(instigator : ActorRef; health : float; delta : float) : void {
        if (health <= 0.0f && !self.Dead) {
            self.Dead = true
            self.ActionSystem.Shutdown()
        }
    }

    [ue_event(name=OnTakeAnyDamage)]
    def OnDamage(damaged : ActorRef; amount : float; kind : ObjectRef; controller : ObjectRef; source : ActorRef) : void {
        self.DamageEvents += 1
        self.LastDamage = amount
        self.LastSource = source
        self.LastController = controller
    }
}
