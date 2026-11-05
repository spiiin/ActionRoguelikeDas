options gen2
module rogue_animation_component public
require rogue_action_system_component public
require rogue_animation_bridge public

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
        let instance = ue_mesh_anim_instance(self.Mesh)
        if (!ue_is_valid(instance)) { return }
        let tags = self.ActionSystem.GetActiveTags()
        rogue_set_animation_state(instance, ue_tags_has(tags, ue_tag("StatusEffect.Sprinting")),
            ue_tags_has(tags, ue_tag("StatusEffect.Stunned")))
        self.StateUpdates += 1
    }
}

typedef RogueAnimationComponentRef = UEObjectRef("rogue.RogueAnimationComponent")
