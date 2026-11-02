options gen2
module rogue_action_host_refs public
require ue_native_gameplay public
[ue_interface_ref(path="/Game/DasRogue/Types/RogueActionHost.RogueActionHost_C", id="rogue.RogueActionHost")]
struct RogueActionHostRef { handle : UObjectHandle }

let ROGUE_ACTION_HOST_INTERFACE = "/Game/DasRogue/Types/RogueActionHost.RogueActionHost_C"

// Load the authored RogueActionHost interface asset before compiling this typed view.

def GetAttributeValue(target : RogueActionHostRef; tag : GameplayTag) : float {
    let call = ue_begin_interface_call(target.handle, ROGUE_ACTION_HOST_INTERFACE, "GetAttributeValue")
    __ue_method_arg_struct(call, "tag", tag.value)
    ue_invoke_call(call)
    let value = ue_result_float(call, "returnvalue")
    ue_release_call(call)
    return value
}

def ApplyAttributeChange(target : RogueActionHostRef; tag : GameplayTag; delta : float) : void {
    let call = ue_begin_interface_call(target.handle, ROGUE_ACTION_HOST_INTERFACE, "ApplyAttributeChange")
    __ue_method_arg_struct(call, "tag", tag.value)
    ue_arg_float(call, "delta", delta)
    ue_invoke_call(call)
    ue_release_call(call)
}

def AppendActiveTags(target : RogueActionHostRef; tags : GameplayTagContainer) : void {
    let call = ue_begin_interface_call(target.handle, ROGUE_ACTION_HOST_INTERFACE, "AppendActiveTags")
    __ue_method_arg_struct(call, "tags", tags.value)
    ue_invoke_call(call)
    ue_release_call(call)
}

def RemoveActiveTags(target : RogueActionHostRef; tags : GameplayTagContainer) : void {
    let call = ue_begin_interface_call(target.handle, ROGUE_ACTION_HOST_INTERFACE, "RemoveActiveTags")
    __ue_method_arg_struct(call, "tags", tags.value)
    ue_invoke_call(call)
    ue_release_call(call)
}

def GetActiveTags(target : RogueActionHostRef) : GameplayTagContainer {
    let call = ue_begin_interface_call(target.handle, ROGUE_ACTION_HOST_INTERFACE, "GetActiveTags")
    ue_invoke_call(call)
    let value = GameplayTagContainer(value = __ue_method_result_struct(call, "returnvalue"))
    ue_release_call(call)
    return value
}

def IsActionOwnerAlive(target : RogueActionHostRef) : bool {
    let call = ue_begin_interface_call(target.handle, ROGUE_ACTION_HOST_INTERFACE, "IsActionOwnerAlive")
    ue_invoke_call(call)
    let value = ue_result_bool(call, "returnvalue")
    ue_release_call(call)
    return value
}

def RogueActionHostRef_raw(value : RogueActionHostRef) : UObjectHandle {
    return ue_cast_interface(value.handle, ROGUE_ACTION_HOST_INTERFACE)
}

def RogueActionHostRef_from(value : UObjectHandle) : RogueActionHostRef {
    return RogueActionHostRef(handle = ue_cast_interface(value, ROGUE_ACTION_HOST_INTERFACE))
}
