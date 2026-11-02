options gen2
module rogue_player_controller public
require ue_native_gameplay public
require rogue_refs public
require rogue_action_system_refs public
require math
require ue_vector_math public

// Adapted from Tom Looman's RoguePlayerController, commit 992f860.
// Game behavior lives in daScript; PlayerController is the generic DasForUE host.
[ue_class(module_id="rogue", Blueprintable)]
class RoguePlayerController : PlayerController {
    @ue_component
    InteractionComponent : RogueInteractionComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Input") {
        var Controls : InputMappingContextRef
        var Input_Interact : InputActionRef
        var TeamId : int = 1
        var Input_Fire : InputActionRef
    }

    defaults = ue_defaults() {
        self.Controls = ue_asset_default("/Game/DasRogue/Input/IMC_Rogue.IMC_Rogue")
        self.Input_Interact = ue_asset_default("/Game/DasRogue/Input/IA_Interact.IA_Interact")
        self.Input_Fire = ue_asset_default("/Game/DasRogue/Input/IA_Fire.IA_Fire")
    }

    state = ue_properties(BlueprintReadWrite) {
        var ControlsBound : bool = false
        var FireBound : bool = false
        var InteractPresses : int = 0
        var SuccessfulInteractions : int = 0
    }

    def BeginPlay() : void {
        ue_controller_set_team(ue_ref(type<PlayerControllerRef>, ue_self_object()), self.TeamId)
        self.TryBindControls()
    }

    def Tick(delta : float) : void {
        if (!self.ControlsBound || !self.FireBound) {
            self.TryBindControls()
        }
    }

    def TryBindControls() : void {
        let player = ue_ref(type<PlayerControllerRef>, ue_self_object())
        let hasInputs = ue_is_valid(self.Controls) && ue_is_valid(self.Input_Interact) && ue_is_valid(self.Input_Fire)
        if (!hasInputs || !ue_player_controls_ready(player)) { return }
        if (self.ControlsBound && self.FireBound) { return }
        ue_enhanced_add_context(player, self.Controls, 0)
        ue_bind_inputs()
        self.ControlsBound = true
        self.FireBound = true
    }

    [ue_input(action="Input_Fire", Started)]
    def OnFire(value : bool) : void {
        if (!value) { return }
        let pawn = ue_ref(type<PlayerControllerRef>, ue_self_object()).K2_GetPawn()
        if (!ue_is_valid(pawn)) { return }
        let component = ue_component_get(type<RogueActionSystemComponentRef>,
            ue_ref(type<ActorRef>, pawn.handle), "ActionSystem")
        if (ue_is_valid(component)) { component.StartAction(ue_tag("Action.PrimaryAttack")) }
    }

    [ue_input(action="Input_Interact", Started)]
    def OnInteract(value : bool) : void {
        if (!value) { return }
        self.InteractPresses += 1
        if (self.InteractionComponent.Interact()) { self.SuccessfulInteractions += 1 }
    }
}
