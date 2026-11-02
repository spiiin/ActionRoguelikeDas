options gen2
require rogue_target_dummy public
require rogue_attribute_refs public
require rogue_action_events public
require rogue_action_system_refs public

[ue_class(module_id="roguedemo", Blueprintable)]
class RogueCombatTarget : RogueTargetDummy {
    @ue_component
    ActionSystem : RogueActionSystemComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Overwhelm") {
        var OverwhelmClass : ObjectClass
    }

    defaults = ue_defaults() {
        self.OverwhelmClass = ue_class_default("/Game/DasRogue/Actions/BP_RogueActionEffectOverwhelm.BP_RogueActionEffectOverwhelm_C")
    }

    def override BeginPlay() : void {
        Super.BeginPlay()
        self.Attributes.OnHealthChanged.RemoveUFunction(ue_self_object(), "OnHealthChanged")
        if (ue_class_valid(self.OverwhelmClass)) { self.ActionSystem.GrantAction(self.OverwhelmClass) }
        self.RefreshStatus()
    }

    def EndPlay(reason : int) : void {
        // Managed ue_event subscriptions are released by the actor lifecycle.
        if (ue_is_valid(self.ActionSystem)) { self.ActionSystem.Shutdown() }
    }

    [ue_event(source="Attributes", name="OnHealthChanged")]
    def OnCombatHealthChanged(instigator : ActorRef; newHealth : float; delta : float) : void {
        self.OnHealthChanged(instigator, newHealth, delta)
        if (newHealth <= 0.0f) { self.ActionSystem.Shutdown() }
        self.RefreshStatus()
    }

    [ue_event(source="ActionSystem", name="GameplayTagUpdated")]
    def OnStatusChanged(tag : GameplayTag; count : int) : void { self.RefreshStatus() }

    [ue_function(BlueprintCallable)]
    def RefreshStatus() : void {
        let stunned = ue_tags_has(self.ActionSystem.GetActiveTags(), ue_tag("StatusEffect.Stunned"))
        let status = self.Dead ? "DEAD" : stunned ? "STUNNED" : "Overwhelm target"
        self.Label.K2_SetText(ue_text_invariant("{status} | HP: {int(self.Attributes.Health)} / {int(self.Attributes.HealthMax)}"))
    }
}
