options gen2
module rogue_director_host public
require ue_native_gameplay public

[ue_interface(module_id="rogue", BlueprintType)]
class RogueDirectorHost {
    [ue_function(BlueprintCallable)]
    def ReserveSlot(index : int) : bool {}

    [ue_function(BlueprintCallable)]
    def ReleaseSlot(index : int) : void {}

    [ue_function(BlueprintCallable)]
    def SpawnReserved(index : int; data : ObjectRef; location : UEVector) : bool {}
}

