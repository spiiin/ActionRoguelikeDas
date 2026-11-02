options gen2
module rogue_attribute_component public
require rogue_attribute_events public
require math

// Health slice of Tom Looman's ActionRoguelike attribute system.
// Publication permission and redistribution license are pending.
[ue_class(module_id="rogue", Blueprintable)]
class RogueAttributeComponent : ActorComponent {

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Attributes") {
        var HealthMax : float = 100.0f
    }

    state = ue_properties(BlueprintReadWrite, Category = "Attributes") {
        var Health : float = 100.0f
        var LastInstigator : ActorRef
        var HealthChanges : int = 0
    }

    events = ue_properties(BlueprintAssignable, Category = "Attributes") {
        var OnHealthChanged : RogueHealthChanged
    }

    def BeginPlay() : void {
        self.HealthMax = max(self.HealthMax, 0.0f)
        self.Health = self.HealthMax
        let call = ue_begin_call(ue_self_object(), "SetComponentTickEnabled")
        ue_arg_bool(call, "bEnabled", false)
        ue_invoke_call(call)
        ue_release_call(call)
    }

    [ue_function(BlueprintCallable, Category="Attributes")]
    def IsAlive() : bool { return self.Health > 0.0f }

    [ue_function(BlueprintCallable, Category="Attributes")]
    def ApplyHealthChange(instigator : ActorRef; delta : float) : bool {
        // NaN and infinity are rejected before mutating state or broadcasting.
        if (!is_finite(delta)) { return false }
        let previousHealth = self.Health
        self.Health = clamp(previousHealth + delta, 0.0f, self.HealthMax)
        let appliedDelta = self.Health - previousHealth
        if (appliedDelta == 0.0f) { return false }
        self.LastInstigator = instigator
        self.HealthChanges += 1
        self.OnHealthChanged.Broadcast(instigator, self.Health, appliedDelta)
        return true
    }

    [ue_event(source=owner, source_type=ActorRef, name="OnTakeAnyDamage")]
    def OnOwnerDamage(damaged : ActorRef; amount : float; kind : ObjectRef; controller : ObjectRef; source : ActorRef) : void {
        if (amount <= 0.0f || !self.IsAlive()) { return }
        var instigator = source
        if (ue_object_valid(source.handle)) {
            let pawn = source.Instigator
            if (ue_object_valid(pawn.handle)) { instigator = ue_ref(type<ActorRef>, pawn.handle) }
        }
        self.ApplyHealthChange(instigator, -amount)
    }
}
