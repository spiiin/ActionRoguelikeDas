options gen2
module rogue_director_config public
require rogue_director_types public

[ue_class(module_id="rogue", Blueprintable)]
class RogueDirectorConfig : DataAsset {
    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Director") {
        var DisplayName : string = "Director"
        var MonsterSpawnTable : RogueSpawnTableRef
        var SpawnLocationQuery : EnvQueryRef
        var CreditGainCurve : RogueIncomeCurveRef
        var CreditsPerSecond : float = 2.0f
        var StartingCredits : float = 0.0f
        var TickInterval : float = 0.5f
        var TimeBetweenWaves : float = 6.0f
    }
}

typedef RogueDirectorConfigRef = UEObjectRef("rogue.RogueDirectorConfig")
