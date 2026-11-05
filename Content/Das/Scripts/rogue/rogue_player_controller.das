options gen2
module rogue_player_controller public
require rogue_tags public
require ue_native_gameplay public
require rogue_interaction_component public
require rogue_action_system_component public
require rogue_hud_component public
require math
require ue_vector_math public

// Adapted from Tom Looman's RoguePlayerController, commit 992f860.
// Game behavior lives in daScript; PlayerController is the generic DasForUE host.
[ue_class(module_id="rogue", Blueprintable)]
class RoguePlayerController : PlayerController {
    @ue_component
    HUD : RogueHUDComponentRef

    @ue_component
    InteractionComponent : RogueInteractionComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Input") {
        var Controls : InputMappingContextRef
        var Input_Interact : InputActionRef
        var TeamId : int = 1
        var Input_Fire : InputActionRef
        var Input_SecondaryAttack : InputActionRef
        var Input_SpecialAttack : InputActionRef
    }

    defaults = ue_defaults() {
        self.Controls = ue_asset_default("/Game/DasRogue/Input/IMC_Rogue.IMC_Rogue")
        self.Input_Interact = ue_asset_default("/Game/DasRogue/Input/IA_Interact.IA_Interact")
        self.Input_Fire = ue_asset_default("/Game/DasRogue/Input/IA_Fire.IA_Fire")
        self.Input_SecondaryAttack = ue_asset_default("/Game/DasRogue/Input/IA_SecondaryAttack.IA_SecondaryAttack")
        self.Input_SpecialAttack = ue_asset_default("/Game/DasRogue/Input/IA_SpecialAttack.IA_SpecialAttack")
    }

    state = ue_properties(BlueprintReadWrite) {
        var ControlsBound : bool = false
        var InputSetups : int = 0
        var InteractPresses : int = 0
        var SuccessfulInteractions : int = 0
    }

    def BeginPlay() : void {
        ue_controller_set_team(ue_ref(type<PlayerControllerRef>, ue_self_object()), self.TeamId)
    }

    [ue_function(BlueprintEvent)]
    def SetupInputComponent() : void {
        self.ControlsBound = false
        let player = ue_ref(type<PlayerControllerRef>, ue_self_object())
        verify(ue_is_valid(self.Controls) && ue_is_valid(self.Input_Interact) && ue_is_valid(self.Input_Fire),
            "Controller input assets are not configured")
        verify(ue_is_valid(self.Input_SecondaryAttack) && ue_is_valid(self.Input_SpecialAttack),
            "Additional attack input assets are not configured")
        verify(ue_player_controls_ready(player), "SetupInputComponent requires local Enhanced Input")
        ue_enhanced_add_context(player, self.Controls, 0)
        ue_bind_inputs()
        self.ControlsBound = true
        self.InputSetups += 1
    }

    [ue_input(action="Input_Fire", Triggered)]
    def OnFire(value : bool) : void {
        if (!value) { return }
        self.StartAttack(rogue_tag_primary_attack())
    }

    [ue_input(action="Input_SecondaryAttack", Triggered)]
    def OnSecondaryAttack(value : bool) : void {
        if (value) { self.StartAttack(rogue_tag_secondary_attack()) }
    }

    [ue_input(action="Input_SpecialAttack", Triggered)]
    def OnSpecialAttack(value : bool) : void {
        if (value) { self.StartAttack(rogue_tag_special_attack()) }
    }

    def StartAttack(name : GameplayTag) : void {
        let pawn = ue_ref(type<PlayerControllerRef>, ue_self_object()).K2_GetPawn()
        if (!ue_is_valid(pawn)) { return }
        let component = ue_component_get(type<RogueActionSystemComponentRef>,
            ue_ref(type<ActorRef>, pawn.handle), "ActionSystem")
        if (ue_is_valid(component)) { component.StartAction(name) }
    }

    [ue_input(action="Input_Interact", Started)]
    def OnInteract(value : bool) : void {
        if (!value) { return }
        self.InteractPresses += 1
        if (self.InteractionComponent.Interact()) { self.SuccessfulInteractions += 1 }
    }
}
