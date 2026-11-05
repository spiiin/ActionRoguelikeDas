options gen2
module rogue_course_world public
require rogue_lever public
require rogue_projectile_spammer public
require rogue_coin_test_actor public
require rogue_spawn_director public

typedef CourseCoinSourceRef = UEObjectRef("roguedemo.RogueCoinTestActor")

// Exact two connections from P_OpenWorldTestMap's Level Blueprint.
[ue_class(module_id="roguedemo", Blueprintable)]
class RogueCourseWorld : Actor {
    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Course map") {
        var SpammerLever : RogueLeverRef
        var CoinLever : RogueLeverRef
        var Spammer : RogueProjectileSpammerRef
        var CoinSource : CourseCoinSourceRef
        var Director : RogueSpawnDirectorRef
        // Original Rogue.SpawningEnabled is false by default.
        var SpawnWaves : bool = false
        var CoinsPerPull : int = 1000
        // Assigned on the ignored local map, keeping acquired assets out of public defaults.
        var CoinMesh : StaticMeshRef
        var CoinSound : SoundBaseRef
        var CoinPickupTrigger : string = "CoinPickedUp"
    }

    state = ue_properties(BlueprintReadWrite) {
        var SpammerStarts : int = 0
        var CoinBatches : int = 0
    }

    def BeginPlay() : void {
        self.ConfigureCoinPresentation()
        if (ue_is_valid(self.SpammerLever)) { self.SpammerLever.OnHandlePulled += self.StartSpammer }
        if (ue_is_valid(self.CoinLever)) { self.CoinLever.OnHandlePulled += self.SpawnCoins }
        if (ue_is_valid(self.Director)) { self.Director.SetEnabled(self.SpawnWaves) }
        self.SetActorTickEnabled(false)
    }

    def ConfigureCoinPresentation() : void {
        if (!ue_is_valid(self.CoinSource) || !ue_is_valid(self.CoinMesh)) { return }
        let coins = ue_subsystem(type<RogueCoinPickupSubsystemRef>, self.CoinSource.CoinSystemClass)
        coins.CoinMesh = self.CoinMesh
        // Use the mesh's original material, including its vertex animation.
        coins.CoinMaterial = default<CoinMaterialRef>
        coins.MeshScale = UE_VECTOR_ONE
        coins.VisualOffset = ue_vector(0.0lf, 0.0lf, 50.0lf)
        coins.CoinSound = self.CoinSound
        coins.PickupTrigger = self.CoinPickupTrigger
    }

    def StartSpammer() : void {
        if (ue_is_valid(self.Spammer)) { self.Spammer.StartSpawning(); self.SpammerStarts += 1 }
    }

    def SpawnCoins() : void {
        if (ue_is_valid(self.CoinSource) && self.CoinSource.SpawnCoins(self.CoinsPerPull)) { self.CoinBatches += 1 }
    }

    def EndPlay(reason : int) : void {
        if (ue_is_valid(self.SpammerLever)) { self.SpammerLever.OnHandlePulled -= self.StartSpammer }
        if (ue_is_valid(self.CoinLever)) { self.CoinLever.OnHandlePulled -= self.SpawnCoins }
    }
}
