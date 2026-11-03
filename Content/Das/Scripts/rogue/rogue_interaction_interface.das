options gen2
module rogue_interaction_interface public
require ue_dsl public

// Adapted from Tom Looman's ActionRoguelike, commit 992f860.
// Publication permission and redistribution license are pending.
[ue_interface(module_id="rogue", BlueprintType)]
class RogueInteractionInterface {

    [ue_function(BlueprintCallable, Category="Interaction")]
    def Interact() : void {}
}
