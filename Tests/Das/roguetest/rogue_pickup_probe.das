options gen2
module rogue_pickup_probe public
require rogue_action_probe public
require rogue_health_pickup public

[ue_class(module_id="roguetest", type_folder="/Game/DasRogue/Types", Blueprintable)]
class RoguePickupProbe : RogueActionProbe {
    state = ue_properties(BlueprintReadWrite) {
        var WatchedPickup : RoguePickupActorRef
        var Target : ActorRef
        var ObservedAttributes : RogueAttributeComponentRef
        var ReentrantAttempts : int = 0
        var ReentrantAccepted : bool = false
    }

    [ue_function(BlueprintCallable)]
    def Arm(pickup : ActorRef; target : ActorRef) : void {
        if (ue_is_valid(self.ObservedAttributes)) { self.ObservedAttributes.OnHealthChanged -= self.OnHealed }
        self.WatchedPickup = ue_ref(type<RoguePickupActorRef>, pickup.handle)
        self.Target = target
        self.ObservedAttributes = default<RogueAttributeComponentRef>
        if (ue_is_valid(target)) { self.ObservedAttributes = ue_component_find(type<RogueAttributeComponentRef>, target) }
        if (ue_is_valid(self.ObservedAttributes)) { self.ObservedAttributes.OnHealthChanged += self.OnHealed }
    }

    def OnHealed(instigator : ActorRef; health : float; delta : float) : void {
        if (delta > 0.0f && ue_is_valid(self.WatchedPickup)) {
            self.ReentrantAttempts += 1
            self.ReentrantAccepted = self.WatchedPickup.TryCollect(self.Target)
        }
    }

    [ue_function(BlueprintCallable)]
    def SetHealth(target : ActorRef; health : float) : void {
        let attributes = ue_component_find(type<RogueAttributeComponentRef>, target)
        attributes.ModifyAttribute(ue_tag("Attribute.Health"), health, RogueAttributeModifyType.OverrideBase, default<ActorRef>)
    }

    [ue_function(BlueprintCallable)]
    def SetRespawnDelay(actor : ActorRef; delay : float) : void {
        ue_ref(type<RoguePickupActorRef>, actor.handle).RespawnDelay = delay
    }

    [ue_function(BlueprintCallable)]
    def SetHealingAmount(actor : ActorRef; amount : float) : void {
        ue_ref(type<RogueHealthPickupRef>, actor.handle).HealingAmount = amount
    }
}
