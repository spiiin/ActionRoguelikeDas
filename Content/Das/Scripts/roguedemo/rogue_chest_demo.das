options gen2
require rogue_item_chest
require rogue_interaction

[ue_class(module_id="roguedemo", Blueprintable)]
class RogueChestDemo : RogueItemChest {

    def override BeginPlay() : void { Super.BeginPlay() }

    [ue_function(BlueprintCallable)]
    def OpenDemoChest() : void { rogue_interact(ue_ref(type<ActorRef>, ue_self_object())) }
}
