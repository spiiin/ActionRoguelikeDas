options gen2
module rogue_director_types public
require ue_soft_references public
require ue_environment_queries public
require ue_float_curves public

typedef RogueSpawnTableRef = UENativeObjectRef("/Script/Engine.DataTable")
typedef RogueIncomeCurveRef = CurveFloatRef

[ue_struct(module_id="rogue", BlueprintType)]
struct RogueMonsterSpawnData {
    @ue_property=(EditAnywhere, BlueprintReadWrite)
    MonsterData : SoftObject

    @ue_property=(EditAnywhere, BlueprintReadWrite)
    SpawnCost : float = 0.0f

    @ue_property=(EditAnywhere, BlueprintReadWrite)
    SpawnWeight : float = 1.0f
}

def rogue_director_authority() : bool {
    return ue_actor_has_authority(ue_self_actor())
}

def rogue_director_income(curve : RogueIncomeCurveRef; time, fallback : float) : float {
    if (!ue_is_valid(curve)) { return fallback }
    return ue_curve_float_value(curve, time)
}
