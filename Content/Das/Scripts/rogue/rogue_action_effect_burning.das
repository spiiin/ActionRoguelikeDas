options gen2
module rogue_action_effect_burning public
require rogue_action_effect public
require ue_gameplay_services public
require math

// ActionEffect_Burning Blueprint from course revision 992f860.
// Native ApplyDamage intentionally has no instigator/causer, matching its unwired pins.
[ue_class(module_id="rogue", Blueprintable)]
class RogueActionEffectBurning : RogueActionEffect {
    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Burning") {
        var DamageToApply : float = 5.0f
    }

    state = ue_properties(BlueprintReadWrite) {
        var DamageTicks : int = 0
        var LastDamageApplied : float = 0.0f
        var TotalDamageApplied : float = 0.0f
    }

    defaults = ue_defaults() {
        self.DisplayName = "Burning"
        self.Duration = 3.0f
        self.Period = 1.0f
        self.ResetDurationOnStackIncrease = true
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override ExecutePeriodicEffect() : void {
        Super.ExecutePeriodicEffect()
        if (!self.bIsRunning || !ue_is_valid(self.Host) || !self.Host.IsActionOwnerAlive()) { return }
        let target = ue_ref(type<ActorRef>, ue_component_owner(self.Host.handle))
        let damage = self.DamageToApply * float(self.StackCount)
        if (!ue_is_valid(target) || !is_finite(damage) || damage <= 0.0f) { return }
        self.DamageTicks += 1
        self.LastDamageApplied = ue_apply_damage(target, damage)
        self.TotalDamageApplied += self.LastDamageApplied
    }
}

typedef RogueActionEffectBurningRef = UEObjectRef("rogue.RogueActionEffectBurning")
