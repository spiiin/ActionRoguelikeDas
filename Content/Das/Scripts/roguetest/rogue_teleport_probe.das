options gen2
module rogue_teleport_probe public
require rogue_projectile_teleport public

[ue_class(module_id="roguetest", Blueprintable)]
class RogueTeleportProbe : Actor {
    @ue_component
    @RootComponent
    Root : SceneComponentRef

    state = ue_properties(BlueprintReadWrite) {
        var Observed : RogueProjectileTeleportRef
        var Attempts : int = 0
        var Success : bool = false
    }

    [ue_function(BlueprintCallable)]
    def Watch(actor : ActorRef) : void {
        self.Observed = ue_ref(type<RogueProjectileTeleportRef>, actor.handle)
        self.Attempts = 0
        self.Success = false
    }

    def Tick(delta : float) : void {
        if (!ue_is_valid(self.Observed)) { return }
        self.Attempts = self.Observed.TeleportAttempts
        self.Success = self.Observed.TeleportSucceeded
    }

    [ue_function(BlueprintCallable)]
    def Spawn(kind : ActorClass; location : UEVector; pawn : NativePawnRef) : ActorRef {
        return ue_actor_spawn(type<ActorRef>, kind,
            ue_transform(location, UE_ROTATOR_ZERO, UE_VECTOR_ONE), default<ActorRef>, "AlwaysSpawn", pawn)
    }

    [ue_function(BlueprintCallable)]
    def SpawnPawn(location : UEVector) : NativePawnRef {
        let kind = ue_class_loaded(type<NativePawnRef>, "/Script/Engine.DefaultPawn")
        return ue_actor_spawn(type<NativePawnRef>, kind,
            ue_transform(location, UE_ROTATOR_ZERO, UE_VECTOR_ONE), default<ActorRef>, "AlwaysSpawn")
    }
}
