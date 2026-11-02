options gen2
module rogue_action_effect public
require rogue_action public
require rogue_action_system_refs public

// Adapted from Tom Looman's RogueActionEffect, commit 992f860.
// Publication permission and redistribution license are pending.
[ue_class(module_id="rogue", Blueprintable)]
class RogueActionEffect : RogueAction {

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Effect") {
        // Zero duration means the effect stays active until explicitly stopped.
        var Duration : float = 0.0f
        var Period : float = 0.0f
        var ResetDurationOnStackIncrease : bool = true
    }

    state = ue_properties(BlueprintReadWrite) {
        var StackCount : int = 1
        var PeriodicExecutions : int = 0
        var Stopping : bool = false
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override IsEffect() : bool { return true }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override StartAction() : void {
        Super.StartAction()
        self.ResetDuration()
        if (self.Period > 0.0f) { ue_timer_start("EffectPeriod", self.Period, self.PeriodElapsed, true) }
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override StopAction() : void {
        if (!self.bIsRunning || self.Stopping) { return }
        self.Stopping = true
        let remaining = ue_timer_remaining("EffectPeriod")
        // Preserve the last due tick when duration and period expire together.
        if (self.Period > 0.0f && remaining >= 0.0f && remaining < 0.0001f) { self.PeriodElapsed() }
        ue_timer_cancel("EffectDuration")
        ue_timer_cancel("EffectPeriod")
        Super.StopAction()
        let owner = ue_ref(type<RogueActionSystemComponentRef>, self.Host.handle)
        if (ue_is_valid(owner)) { owner.RemoveAction(ue_ref(type<RogueActionRef>, ue_self_object())) }
        self.Stopping = false
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override IncrementStackSize() : void {
        if (!self.bIsRunning || self.Stopping) { return }
        self.StackCount += 1
        if (self.ResetDurationOnStackIncrease) { self.ResetDuration() }
    }

    [ue_function(BlueprintCallable)]
    def ResetDuration() : void {
        if (self.Duration > 0.0f) { ue_timer_start("EffectDuration", self.Duration, self.DurationElapsed, false) }
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def DurationElapsed() : void { self.StopAction() }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def PeriodElapsed() : void {
        if (!self.bIsRunning) { return }
        self.PeriodicExecutions += 1
        self.ExecutePeriodicEffect()
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def ExecutePeriodicEffect() : void {}
}
