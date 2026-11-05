options gen2
module rogue_animation_bridge public
require ue_animation public

// Optional course Anim Blueprint integration; the asset's generated method is dynamic.
def rogue_set_animation_state(instance : AnimInstanceRef; sprinting, stunned : bool) : void {
    with_ue_call(instance.handle, "SetGameplayAnimationState") $(call) {
        ue_arg(call, "Sprinting", sprinting)
        ue_arg(call, "Stunned", stunned)
        ue_invoke_call(call)
    }
}
