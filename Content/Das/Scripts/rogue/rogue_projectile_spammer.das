options gen2
module rogue_projectile_spammer public
require ue_vector_math public
require ue_native_gameplay public
require math

// Arrow is an ordinary native scene component; no custom host is needed.
typedef RogueArrowRef = UENativeObjectRef("/Script/Engine.ArrowComponent")

// BP_ProjectileSpammer, course commit 992f860. Native actor ticking supplies cadence.
[ue_class(module_id="rogue", Blueprintable)]
class RogueProjectileSpammer : Pawn {
    @ue_component
    @RootComponent
    SceneRoot : SceneComponentRef

    @ue_component
    @Attach="SceneRoot"
    Arrow : RogueArrowRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Spawning") {
        var ProjectileClass : ActorClass
        var SpawnInterval : float = 0.5f
    }

    state = ue_properties(BlueprintReadWrite) {
        var Spawning : bool = false
        var SpawnAttempts : int = 0
        var ProjectilesSpawned : int = 0
        var LastProjectile : ActorRef
    }

    defaults = ue_defaults() {
        self.ProjectileClass = ue_class_default("/Game/DasRogue/BP_MagicProjectileDemo.BP_MagicProjectileDemo_C")
    }

    def BeginPlay() : void {
        ue_self_actor().SetActorTickInterval(max(0.0f, self.SpawnInterval))
        ue_self_actor().SetActorTickEnabled(false)
    }

    [ue_function(BlueprintCallable)]
    def StartSpawning() : void {
        self.Spawning = true
        ue_self_actor().SetActorTickEnabled(true)
    }

    [ue_function(BlueprintCallable)]
    def StopSpawning() : void {
        self.Spawning = false
        ue_self_actor().SetActorTickEnabled(false)
    }

    def Tick(delta : float) : void {
        if (!self.Spawning || !ue_class_valid(self.ProjectileClass)) { return }
        self.SpawnAttempts += 1
        let arrow = ue_ref(type<SceneComponentRef>, self.Arrow.handle)
        self.LastProjectile = ue_actor_spawn(type<ActorRef>, self.ProjectileClass,
            arrow.K2_GetComponentToWorld(), default<ActorRef>, "Undefined",
            ue_ref(type<NativePawnRef>, ue_self_object()))
        if (ue_is_valid(self.LastProjectile)) { self.ProjectilesSpawned += 1 }
    }

    def EndPlay(reason : int) : void { self.Spawning = false }
}

typedef RogueProjectileSpammerRef = UEObjectRef("rogue.RogueProjectileSpammer")
