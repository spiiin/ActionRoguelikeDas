options gen2
module rogue_coin_test_actor public
require rogue_coin_pickup_subsystem public
require ue_navigation public

[ue_class(module_id="roguedemo", Blueprintable)]
class RogueCoinTestActor : Actor {
    @ue_component
    @RootComponent
    SceneRoot : SceneComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Coins") {
        var CoinSystemClass : ObjectClass
        var SpawnRadius : float = 1024.0f
        var InitialCoinCount : int = 0
    }

    def BeginPlay() : void {
        ue_self_actor().SetActorTickEnabled(false)
        if (self.InitialCoinCount > 0) { self.SpawnCoins(self.InitialCoinCount) }
    }

    [ue_function(BlueprintCallable)]
    def SpawnCoins(count : int) : bool {
        if (!ue_class_valid(self.CoinSystemClass) || count < 0) { return false }
        let coins = ue_subsystem(type<RogueCoinPickupSubsystemRef>, self.CoinSystemClass)
        let origin = ue_self_actor().K2_GetActorLocation()
        var locations : array<UEVector>
        var amounts : array<int>
        for (index in range(count)) {
            let point = ue_navigation_random_point(origin, max(self.SpawnRadius, 0.0f))
            push(locations, point.Found ? point.Location : origin)
            push(amounts, 10)
        }
        return coins.AddCoinPickups(locations, amounts)
    }
}
