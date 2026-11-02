options gen2
module rogue_item_chest public
require ue_native_gameplay public
require math

// Adapted from Tom Looman's ARogueItemChest, commit 992f860.
// https://github.com/tomlooman/ActionRoguelike
// Publication permission and redistribution license are pending.
[ue_class(module_id="rogue", Blueprintable),
 ue_implements(interface="/Game/DasRogue/Types/RogueInteractionInterface.RogueInteractionInterface_C")]
class RogueItemChest : Actor {
    @ue_component
    @RootComponent
    BaseMeshComponent : StaticMeshComponentRef

    @ue_component
    @Attach = "BaseMeshComponent"
    LidMeshComponent : StaticMeshComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Animation") {
        var AnimationSpeed : float = 50.0f
        var AnimationTargetPitch : float = 120.0f
    }

    state = ue_properties(BlueprintReadWrite) {
        var CurrentAnimationPitch : float = 0.0f
    }

    def BeginPlay() : void {
        self.BaseMeshComponent.SetCollisionProfileName(ue_name_value("Interaction"), true)
        self.LidMeshComponent.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        let actor = ue_ref(type<ActorRef>, ue_self_object())
        actor.SetActorTickEnabled(false)
    }

    [ue_function(BlueprintCallable, Category="Interaction")]
    def Interact() : void {
        let actor = ue_ref(type<ActorRef>, ue_self_object())
        actor.SetActorTickEnabled(true)
    }

    def Tick(delta : float) : void {
        // FInterpConstantTo semantics, including signed movement and no overshoot.
        let distance = self.AnimationTargetPitch - self.CurrentAnimationPitch
        if (distance * distance < 1.0e-8f) {
            self.CurrentAnimationPitch = self.AnimationTargetPitch
        } else {
            let step = self.AnimationSpeed * delta
            self.CurrentAnimationPitch += clamp(distance, -step, step)
        }
        let lid = ue_ref(type<SceneComponentRef>, self.LidMeshComponent.handle)
        let rotation = ue_rotator(double(self.CurrentAnimationPitch), 0.0lf, 0.0lf)
        ue_scene_set_relative_rotation(lid, rotation)
        if (abs(self.CurrentAnimationPitch - self.AnimationTargetPitch) <= 1.0e-8f) {
            let actor = ue_ref(type<ActorRef>, ue_self_object())
            actor.SetActorTickEnabled(false)
            self.ChestAnimationComplete()
        }
    }

    // Calls go through ProcessEvent, allowing child Blueprint overrides.
    [ue_function(BlueprintEvent, Category="Animation")]
    def ChestAnimationComplete() : void {}
}
