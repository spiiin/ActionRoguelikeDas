options gen2
module rogue_action_effect_overwhelm public
require rogue_action_effect public
require rogue_attribute_component public
require rogue_effect_helpers public

// Adapted from Tom Looman's RogueActionEffect_Overwhelm, commit 992f860.
[ue_class(module_id="rogue", Blueprintable)]
class RogueActionEffectOverwhelm : RogueActionEffect {

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Overwhelm") {
        var DamageThreshold : float = 20.0f
        var TimeDeltaThreshold : float = 1.0f
        var EffectOnThreshold : ObjectClass
    }

    state = ue_properties(BlueprintReadWrite) {
        var Attributes : RogueAttributeComponentRef
        var LastDamageTime : double = -1.0lf
        var SummedRecentDamage : float = 0.0f
        var DamageEvents : int = 0
        var EffectsTriggered : int = 0
        var Listening : bool = false
    }

    defaults = ue_defaults() {
        self.EffectOnThreshold = ue_class_default("/Game/DasRogue/Actions/BP_RogueActionEffectStun.BP_RogueActionEffectStun_C")
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override StartAction() : void {
        self.StopListening()
        Super.StartAction()
        let owner = ue_ref(type<ActorRef>, ue_component_owner(self.Host.handle))
        self.Attributes = ue_component_find(type<RogueAttributeComponentRef>, owner)
        if (!ue_is_valid(self.Attributes)) {
            self.StopAction()
            return
        }
        self.LastDamageTime = -1.0lf
        self.SummedRecentDamage = 0.0f
        self.Attributes.OnHealthChanged += self.OnHealthChanged
        self.Listening = true
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override StopAction() : void {
        // Detach before tag/action removal can call other handlers.
        self.StopListening()
        Super.StopAction()
    }

    def StopListening() : void {
        if (self.Listening && ue_is_valid(self.Attributes)) {
            self.Attributes.OnHealthChanged -= self.OnHealthChanged
        }
        self.Listening = false
        self.Attributes = default<RogueAttributeComponentRef>
    }

    [ue_function(BlueprintCallable, BlueprintEvent=false)]
    def OnHealthChanged(instigator : ActorRef; newHealth : float; delta : float) : void {
        if (!self.bIsRunning || !self.Listening) { return }
        if (!self.Host.IsActionOwnerAlive() || newHealth <= 0.0f || delta >= 0.0f) { return }
        if (ue_tags_has(self.Host.GetActiveTags(), ue_tag("StatusEffect.Stunned"))) { return }
        self.DamageEvents += 1

        let damage = -delta
        let now = ue_world_seconds()
        let elapsed = now - self.LastDamageTime
        let inDamageWindow = (self.LastDamageTime >= 0.0lf
            && elapsed >= 0.0lf && elapsed < double(self.TimeDeltaThreshold))
        self.SummedRecentDamage = inDamageWindow ? self.SummedRecentDamage + damage : damage
        self.LastDamageTime = now

        if (self.SummedRecentDamage < self.DamageThreshold) { return }
        if (!rogue_is_effect_class(self.EffectOnThreshold)) { return }

        let system = ue_ref(type<RogueActionSystemComponentRef>, self.Host.handle)
        if (!ue_is_valid(system.GrantAction(self.EffectOnThreshold))) { return }

        self.EffectsTriggered += 1
        self.SummedRecentDamage = 0.0f
        self.LastDamageTime = -1.0lf
    }
}
