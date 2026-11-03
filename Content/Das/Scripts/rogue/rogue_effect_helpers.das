options gen2
module rogue_effect_helpers public
require rogue_action_system_component public
require ue_api_math
require ue_result public

let ROGUE_EFFECT_BASE_CLASS = "/Game/DasRogue/Actions/BP_RogueActionEffect.BP_RogueActionEffect_C"

// Check the configured class before construction or action-added notifications.
def rogue_is_effect_class(kind : ObjectClass) : bool {
    if (!ue_class_valid(kind)) { return false }
    let base = ue_class_loaded(type<ObjectRef>, ROGUE_EFFECT_BASE_CLASS)
    return ue_static(KismetMathLibrary.ClassIsChildOf, kind, base)
}

// Absence of a configured effect is handled by the caller. Here a failure
// explains why a requested effect could not be applied; it is not an exception.
def rogue_apply_hit_effect(other : ActorRef; kind : ObjectClass) : Result<RogueActionRef; string> {
    ue_require(ue_is_valid(other), "Hit target is no longer valid") |> ue_try
    ue_require(rogue_is_effect_class(kind), "Configured hit action is not an effect") |> ue_try
    let system = ue_require_valid(ue_component_find(type<RogueActionSystemComponentRef>, other),
        "Hit target has no action system") |> ue_try
    ue_require(system.Enabled, "Hit target action system is disabled") |> ue_try
    return ue_require_valid(system.GrantAction(kind), "Hit effect was rejected")
}
