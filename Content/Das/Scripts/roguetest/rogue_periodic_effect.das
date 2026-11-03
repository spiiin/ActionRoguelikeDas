options gen2
module rogue_periodic_effect public
require rogue_action_effect public

[ue_class(module_id="roguetest", Blueprintable)]
class RoguePeriodicEffect : RogueActionEffect {

    defaults = ue_defaults() { self.Duration = 0.6f; self.Period = 0.1f }

    settings = ue_properties(EditAnywhere, BlueprintReadWrite) {
        var AmountPerStack : float = 3.0f
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override ExecutePeriodicEffect() : void {
        self.Host.ApplyAttributeChange(ue_tag("Attribute.Rage"), self.AmountPerStack * float(self.StackCount))
    }
}
