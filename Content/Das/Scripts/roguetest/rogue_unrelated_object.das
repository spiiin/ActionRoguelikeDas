options gen2
require ue_dsl

[ue_class(module_id="roguetest", Blueprintable)]
class RogueUnrelatedObject : ScriptObject {
    [ue_function(BlueprintCallable)]
    def Ping() : int { return 42 }
}
