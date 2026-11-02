options gen2
module rogue_action_host_refs public
require ue_native_gameplay public
[ue_interface_ref(path="/Game/DasRogue/Types/RogueActionHost.RogueActionHost_C", id="rogue.RogueActionHost")]
struct RogueActionHostRef { handle : UObjectHandle }

let ROGUE_ACTION_HOST_INTERFACE = "/Game/DasRogue/Types/RogueActionHost.RogueActionHost_C"

def RogueActionHostRef_raw(value : RogueActionHostRef) : UObjectHandle {
    return ue_cast_interface(value.handle, ROGUE_ACTION_HOST_INTERFACE)
}

def RogueActionHostRef_from(value : UObjectHandle) : RogueActionHostRef {
    return RogueActionHostRef(handle = ue_cast_interface(value, ROGUE_ACTION_HOST_INTERFACE))
}
