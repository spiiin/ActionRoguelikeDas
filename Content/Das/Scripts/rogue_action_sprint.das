options gen2
module rogue_action_sprint public
require rogue_action public

// A script-owned sprint example; no course Blueprint assets are used.
[ue_class(module_id="rogue", Blueprintable)]
class RogueActionSprint : RogueAction {

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Sprint") {
        var SpeedMultiplier : float = 1.6f
    }

    state = ue_properties(BlueprintReadWrite) { var AppliedMultiplierDelta : float = 0.0f }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override Setup() : void {
        Super.Setup()
        if (!ue_tag_valid(self.ActionName)) { self.ActionName = ue_tag("Action.Sprint") }
        if (ue_tags_count(self.GrantTags) == 0) { self.GrantTags = ue_tags(ue_tag("StatusEffect.Sprinting")) }
        if (ue_tags_count(self.BlockedTags) == 0) { self.BlockedTags = ue_tags(ue_tag("StatusEffect.Stunned")) }
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override StartAction() : void {
        Super.StartAction()
        self.AppliedMultiplierDelta = self.SpeedMultiplier - 1.0f
        self.Host.ApplyAttributeChange(ue_tag("Attribute.MoveSpeedMultiplier"), self.AppliedMultiplierDelta)
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override StopAction() : void {
        self.Host.ApplyAttributeChange(ue_tag("Attribute.MoveSpeedMultiplier"), -self.AppliedMultiplierDelta)
        self.AppliedMultiplierDelta = 0.0f
        Super.StopAction()
    }
}
