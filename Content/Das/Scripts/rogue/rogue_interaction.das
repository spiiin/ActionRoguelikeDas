options gen2
module rogue_interaction public
require ue_object_types public

typedef RogueInteractionRef = UEInterfaceRef("rogue.RogueInteractionInterface")

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
    let interaction = ue_ref(type<RogueInteractionRef>, target.handle)
    interaction.Interact()
    return true
}
