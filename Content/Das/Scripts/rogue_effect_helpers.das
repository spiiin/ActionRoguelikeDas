options gen2
module rogue_effect_helpers public
require rogue_action_system_refs public

let ROGUE_EFFECT_BASE_CLASS = "/Game/DasRogue/Actions/BP_RogueActionEffect.BP_RogueActionEffect_C"

// Check the configured class before construction or action-added notifications.
def rogue_is_effect_class(kind : ObjectClass) : bool {
    if (!ue_class_valid(kind)) { return false }
    let base = ue_class_loaded(type<ObjectRef>, ROGUE_EFFECT_BASE_CLASS)
    let call = ue_begin_static_call("/Script/Engine.KismetMathLibrary", "ClassIsChildOf", "")
    ue_arg_class(call, "testclass", ue_class_handle(kind))
    ue_arg_class(call, "parentclass", ue_class_handle(base))
    ue_invoke_call(call)
    let valid = ue_result_bool(call, "returnvalue")
    ue_release_call(call)
    return valid
}

def rogue_apply_hit_effect(other : ActorRef; kind : ObjectClass) : bool {
    if (!ue_is_valid(other) || !ue_class_valid(kind)) { return false }
    let system = ue_component_find(type<RogueActionSystemComponentRef>, other)
    if (!ue_is_valid(system) || !system.Enabled || !rogue_is_effect_class(kind)) { return false }
    return ue_is_valid(system.GrantAction(kind))
}
