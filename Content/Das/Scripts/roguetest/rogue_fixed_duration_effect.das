options gen2
module rogue_fixed_duration_effect public
require rogue_periodic_effect public

[ue_class(module_id="roguetest", Blueprintable)]
class RogueFixedDurationEffect : RoguePeriodicEffect {

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override Setup() : void {
        Super.Setup()
        self.ResetDurationOnStackIncrease = false
    }
}
