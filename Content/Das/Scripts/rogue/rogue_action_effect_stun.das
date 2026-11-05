options gen2
module rogue_action_effect_stun public
require rogue_tags public
require rogue_action_effect public

[ue_class(module_id="rogue", Blueprintable)]
class RogueActionEffectStun : RogueActionEffect {

    defaults = ue_defaults() {
        self.DisplayName = "Stunned"
        self.Duration = 2.5f
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override Setup() : void {
        Super.Setup()
        var tags = self.GrantTags
        ue_tags_add(tags, rogue_tag_stunned())
        self.GrantTags = tags
    }
}
