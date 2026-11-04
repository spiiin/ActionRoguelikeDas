options gen2
module rogue_animation_component public
require rogue_action_system_component public
require ue_animation public

// The original Anim Blueprint owns pose calculation. This component replaces only
// RogueAnimInstance's gameplay-tag subscription, on the game thread.
[ue_class(module_id="rogue", Blueprintable)]
class RogueAnimationComponent : ActorComponent {
    state = ue_properties(BlueprintReadWrite) {
        var ActionSystem : RogueActionSystemComponentRef
        var Mesh : SkeletalMeshComponentRef
        var Enabled : bool = false
        var StateUpdates : int = 0
    }

    def BeginPlay() : void { self.SetComponentTickEnabled(false) }

    [ue_function(BlueprintCallable)]
    def Configure(mesh : SkeletalMeshComponentRef; enabled : bool) : void {
        if (ue_is_valid(self.ActionSystem)) { self.ActionSystem.GameplayTagUpdated -= self.OnTagUpdated }
        self.Mesh = mesh
        self.Enabled = enabled
        self.ActionSystem = ue_component_find(type<RogueActionSystemComponentRef>,
            ue_ref(type<ActorRef>, ue_component_owner(ue_self_object())))
        if (ue_is_valid(self.ActionSystem)) { self.ActionSystem.GameplayTagUpdated += self.OnTagUpdated }
        self.RefreshState()
    }

    [ue_function]
    def OnTagUpdated(tag : GameplayTag; count : int) : void {
        if (ue_tag_matches(tag, ue_tag("StatusEffect.Sprinting"), false) ||
            ue_tag_matches(tag, ue_tag("StatusEffect.Stunned"), false)) { self.RefreshState() }
    }

    [ue_function(BlueprintCallable)]
    def RefreshState() : void {
        if (!self.Enabled || !ue_is_valid(self.Mesh) || !ue_is_valid(self.ActionSystem)) { return }
        let instanceCall = ue_begin_call(self.Mesh.handle, "GetAnimInstance")
        ue_invoke_call(instanceCall)
        let instance = ue_result_object(instanceCall, "ReturnValue")
        ue_release_call(instanceCall)
        if (!ue_object_valid(instance)) { return }
        let tags = self.ActionSystem.GetActiveTags()
        // A small generated Blueprint method is the boundary to the external asset.
        let call = ue_begin_call(instance, "SetGameplayAnimationState")
        ue_arg(call, "Sprinting", ue_tags_has(tags, ue_tag("StatusEffect.Sprinting")))
        ue_arg(call, "Stunned", ue_tags_has(tags, ue_tag("StatusEffect.Stunned")))
        ue_invoke_call(call)
        ue_release_call(call)
        self.StateUpdates += 1
    }
}

typedef RogueAnimationComponentRef = UEObjectRef("rogue.RogueAnimationComponent")
