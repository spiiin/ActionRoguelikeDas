options gen2
module rogue_monster_data public
require rogue_action public

[ue_class(module_id="rogue", Blueprintable)]
class RogueMonsterData : DataAsset {
    @ue_property=(EditAnywhere, BlueprintReadWrite)
    @Category="Monster"
    @ue_class_base="/Script/Engine.Pawn"
    MonsterClass : UEClassHandle

    @ue_property=(EditAnywhere, BlueprintReadWrite)
    @Category="Monster"
    @ue_class_base="/Script/UMG.UserWidget"
    HealthWidgetClass : UEClassHandle

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Monster") {
        var Actions : array<ObjectClass>
        var LootCoins : int = 100
    }
}

typedef RogueMonsterDataRef = UEObjectRef("rogue.RogueMonsterData")
