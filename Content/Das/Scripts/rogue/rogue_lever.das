options gen2
module rogue_lever public
require ue_native_gameplay public
require ue_projectile_components public

[ue_multicast]
struct RogueHandlePulled {
    signature : function<() : void>
}

// BP_Lever, course commit 992f860: every interaction broadcasts, with no latch.
[ue_class(module_id="rogue", type_folder="/Game/DasRogue/Types", Blueprintable),
 ue_implements(interface="/Game/DasRogue/Types/RogueInteractionInterface.RogueInteractionInterface_C")]
class RogueLever : Actor {
    @ue_component
    @RootComponent
    SceneRoot : SceneComponentRef

    @ue_component
    @Attach="SceneRoot"
    SwitchBaseMeshComp : StaticMeshComponentRef

    @ue_component
    @Attach="SwitchBaseMeshComp"
    HandleMeshComp : StaticMeshComponentRef

    @ue_component
    @Attach="SceneRoot"
    InteractionSphere : SphereComponentRef

    events = ue_properties(BlueprintAssignable) {
        var OnHandlePulled : RogueHandlePulled
    }

    state = ue_properties(BlueprintReadWrite) {
        var Pulls : int = 0
    }

    def BeginPlay() : void {
        self.InteractionSphere.SetCollisionProfileName(ue_name_value("Interaction"), true)
        self.SwitchBaseMeshComp.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        self.HandleMeshComp.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        self.SetActorTickEnabled(false)
    }

    [ue_function(BlueprintCallable, Category="Interaction")]
    def Interact() : void {
        self.Pulls += 1
        self.OnHandlePulled.Broadcast()
    }
}

typedef RogueLeverRef = UEObjectRef("rogue.RogueLever")
