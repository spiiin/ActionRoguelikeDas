options gen2
module rogue_interaction public
require ue_object_types public

let ROGUE_INTERACTION_INTERFACE = "/Game/DasRogue/Types/RogueInteractionInterface.RogueInteractionInterface_C"

// Original interaction contract has no interactor argument.
// The generic DasForUE sample ue_interact uses a different interface signature.
def rogue_can_interact(target : ActorRef) : bool {
    return ue_is_valid(target) && ue_implements_interface(target.handle, ROGUE_INTERACTION_INTERFACE)
}

def rogue_interact(target : ActorRef) : bool {
    if (!rogue_can_interact(target)) {
        return false
    }
    let call = ue_begin_interface_call(target.handle, ROGUE_INTERACTION_INTERFACE, "Interact")
    ue_invoke_call(call)
    ue_release_call(call)
    return true
}
