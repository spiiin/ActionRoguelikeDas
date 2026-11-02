options gen2
module rogue_action_host_interface public
require ue_native_gameplay public

[ue_interface(module_id="rogue", BlueprintType)]
class RogueActionHost {

    [ue_function(BlueprintCallable)]
    def GetAttributeValue(tag : GameplayTag) : float {}

    [ue_function(BlueprintCallable)]
    def ApplyAttributeChange(tag : GameplayTag; delta : float) : void {}

    [ue_function(BlueprintCallable)]
    def AppendActiveTags(tags : GameplayTagContainer) : void {}

    [ue_function(BlueprintCallable)]
    def RemoveActiveTags(tags : GameplayTagContainer) : void {}

    [ue_function(BlueprintCallable)]
    def GetActiveTags() : GameplayTagContainer {}

    [ue_function(BlueprintCallable)]
    def IsActionOwnerAlive() : bool {}
}
