options gen2
module rogue_effect_helpers public
require rogue_action_system_component public
require ue_api_math

let ROGUE_EFFECT_BASE_CLASS = "/Game/DasRogue/Actions/BP_RogueActionEffect.BP_RogueActionEffect_C"

// Check the configured class before construction or action-added notifications.
def rogue_is_effect_class(kind : ObjectClass) : bool {
    if (!ue_class_valid(kind)) { return false }
    let base = ue_class_loaded(type<ObjectRef>, ROGUE_EFFECT_BASE_CLASS)
    return ue_static(KismetMathLibrary.ClassIsChildOf, kind, base)
}

def rogue_apply_hit_effect(other : ActorRef; kind : ObjectClass) : bool {
    if (!ue_is_valid(other) || !ue_class_valid(kind)) { return false }
    let system = ue_component_find(type<RogueActionSystemComponentRef>, other)
    if (!ue_is_valid(system) || !system.Enabled || !rogue_is_effect_class(kind)) { return false }
    return ue_is_valid(system.GrantAction(kind))
}
