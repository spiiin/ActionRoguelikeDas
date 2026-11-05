options gen2
module rogue_lever_spammer_demo public
require rogue_lever public
require rogue_projectile_spammer public

// Level wiring stays separate from the reusable gameplay classes.
[ue_class(module_id="roguedemo", Blueprintable)]
class RogueLeverSpammerDemo : Actor {
    settings = ue_properties(EditAnywhere, BlueprintReadWrite) {
        var Lever : RogueLeverRef
        var Spammer : RogueProjectileSpammerRef
    }

    state = ue_properties(BlueprintReadWrite) {
        var Activations : int = 0
    }

    def BeginPlay() : void {
        if (ue_is_valid(self.Lever)) { self.Lever.OnHandlePulled += self.OnHandlePulled }
        self.SetActorTickEnabled(false)
    }

    def OnHandlePulled() : void {
        self.Activations += 1
        if (ue_is_valid(self.Spammer)) { self.Spammer.StartSpawning() }
    }

    def EndPlay(reason : int) : void {
        if (ue_is_valid(self.Lever)) { self.Lever.OnHandlePulled -= self.OnHandlePulled }
    }
}
