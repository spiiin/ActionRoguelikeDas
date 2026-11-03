options gen2
module rogue_action_drop_loot public
require rogue_action public
require rogue_coin_pickup_subsystem public
require ue_navigation public
require ue_random public

[ue_class(module_id="rogue", Blueprintable)]
class RogueActionDropLoot : RogueAction {
    lootSettings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Loot") {
        var CoinSystemClass : ObjectClass
        var CreditsToDrop : int = 10
        var MaxCreditsPerCoin : int = 15
        var MaxDropDistance : float = 250.0f
        var PlacementAttempts : int = 4
    }

    lootState = ue_properties(BlueprintReadWrite) {
        var HasDropped : bool = false
        var DroppedCredits : int = 0
        var DroppedCoins : int = 0
        var PlacementFallbacks : int = 0
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override Setup() : void {
        Super.Setup()
        if (!ue_tag_valid(self.ActionName)) { self.ActionName = ue_tag("Action.DropLoot") }
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override StartAction() : void {
        if (self.HasDropped || !ue_is_valid(self.Host) || !ue_class_valid(self.CoinSystemClass)) { return }
        Super.StartAction()
        let owner = ue_ref(type<ActorRef>, ue_component_owner(self.Host.handle))
        if (!ue_is_valid(owner)) { self.StopAction(); return }
        let coins = ue_subsystem(type<RogueCoinPickupSubsystemRef>, self.CoinSystemClass)
        let origin = owner.K2_GetActorLocation()
        var remaining = max(self.CreditsToDrop, 0)
        var seed = int(ue_world_seconds())
        var locations : array<UEVector>
        var amounts : array<int>
        let radius = is_finite(self.MaxDropDistance) ? max(self.MaxDropDistance, 0.0f) : 0.0f
        while (remaining > 0) {
            var location = origin
            var placed = false
            for (attempt in range(max(self.PlacementAttempts, 1))) {
                let point = ue_navigation_random_point(origin, radius)
                if (point.Found) { location = point.Location; placed = true; break }
            }
            if (!placed) { self.PlacementFallbacks += 1 }
            let amount = min(ue_random_int(seed, 1, max(self.MaxCreditsPerCoin, 1)), remaining)
            push(locations, location)
            push(amounts, amount)
            remaining -= amount
        }
        if (coins.AddCoinPickups(locations, amounts)) {
            self.HasDropped = true
            self.DroppedCredits = max(self.CreditsToDrop, 0)
            self.DroppedCoins = length(amounts)
        }
        self.StopAction()
    }
}

typedef RogueActionDropLootRef = UEObjectRef("rogue.RogueActionDropLoot")
