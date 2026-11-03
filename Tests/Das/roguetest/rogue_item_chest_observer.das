options gen2
require rogue_item_chest
require rogue_interaction

[ue_class(module_id="roguetest", Blueprintable)]
class RogueItemChestObserver : RogueItemChest {
    state = ue_properties(BlueprintReadWrite) {
        var CompletionCount : int = 0
    }

    [ue_function(BlueprintCallable)]
    def TryInteract(target : ActorRef) : bool { return rogue_interact(target) }

    [ue_function(BlueprintEvent, Category="Animation")]
    def override ChestAnimationComplete() : void { self.CompletionCount += 1 }
}

