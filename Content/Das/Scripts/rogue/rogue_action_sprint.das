options gen2
module rogue_action_sprint public
require rogue_tags public
require rogue_action public
require rogue_presentation public
require ue_projectile_components public

// Course sprint presentation is optional and supplied by the local profile.
[ue_class(module_id="rogue", Blueprintable)]
class RogueActionSprint : RogueAction {

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Sprint") {
        var SprintEffect : NiagaraSystemRef
        var SprintSound : SoundBaseRef
        var SpeedMultiplier : float = 1.6f
    }

    state = ue_properties(BlueprintReadWrite) {
        var AppliedMultiplierDelta : float = 0.0f
        var LeftHandEffect : NiagaraComponentRef
        var RightHandEffect : NiagaraComponentRef
        var HoverSound : AudioComponentRef
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override Setup() : void {
        Super.Setup()
        if (!ue_tag_valid(self.ActionName)) { self.ActionName = rogue_tag_sprint() }
        if (ue_tags_count(self.GrantTags) == 0) { self.GrantTags = ue_tags(rogue_tag_sprinting()) }
        if (ue_tags_count(self.BlockedTags) == 0) {
            self.BlockedTags = ue_tags(rogue_tag_attacking(), rogue_tag_stunned())
        }
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override StartAction() : void {
        Super.StartAction()
        self.AppliedMultiplierDelta = self.SpeedMultiplier - 1.0f
        self.Host.ApplyAttributeChange(rogue_tag_move_speed_multiplier(), self.AppliedMultiplierDelta)
        if (!ue_is_valid(self.SprintEffect) && !ue_is_valid(self.SprintSound)) { return }
        let owner = ue_ref(type<CharacterRef>, ue_component_owner(self.Host.handle))
        let mesh = ue_ref(type<SceneComponentRef>, owner.Mesh.handle)
        if (ue_is_valid(self.SprintEffect)) {
            self.LeftHandEffect = ue_ref(type<NiagaraComponentRef>, ue_niagara_spawn_attached(self.SprintEffect, mesh, ue_name_value("Muzzle_02"), true))
            self.RightHandEffect = ue_ref(type<NiagaraComponentRef>, ue_niagara_spawn_attached(self.SprintEffect, mesh, ue_name_value("Muzzle_01"), true))
        }
        if (ue_is_valid(self.SprintSound)) {
            self.HoverSound = ue_ref(type<AudioComponentRef>, ue_sound_spawn_attached(self.SprintSound, mesh))
        }
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override StopAction() : void {
        self.Host.ApplyAttributeChange(rogue_tag_move_speed_multiplier(), -self.AppliedMultiplierDelta)
        self.AppliedMultiplierDelta = 0.0f
        if (ue_is_valid(self.LeftHandEffect)) { ue_niagara_release_to_pool(self.LeftHandEffect) }
        if (ue_is_valid(self.RightHandEffect)) { ue_niagara_release_to_pool(self.RightHandEffect) }
        if (ue_is_valid(self.HoverSound)) { ue_audio_trigger(self.HoverSound, "StopHovering") }
        self.LeftHandEffect = default<NiagaraComponentRef>
        self.RightHandEffect = default<NiagaraComponentRef>
        self.HoverSound = default<AudioComponentRef>
        Super.StopAction()
    }
}

typedef RogueActionSprintRef = UEObjectRef("rogue.RogueActionSprint")
