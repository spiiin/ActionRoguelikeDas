options gen2
module rogue_blackhole_probe public
require rogue_projectile_blackhole public

[ue_class(module_id="roguetest", Blueprintable)]
class RogueBlackholeProbe : Actor {
    @ue_component
    @RootComponent
    Root : SceneComponentRef

    def BeginPlay() : void { self.SetActorTickEnabled(false) }

    [ue_function(BlueprintCallable)]
    def Spawn(kind : ActorClass; location : UEVector; stationary : bool) : ActorRef {
        let actor = ue_actor_spawn(type<ActorRef>, kind,
            ue_transform(location, UE_ROTATOR_ZERO, UE_VECTOR_ONE), default<ActorRef>, "AlwaysSpawn")
        if (stationary) {
            let movement = ue_component_find(type<ProjectileMovementComponentRef>, actor)
            let sphere = ue_component_find(type<SphereComponentRef>, actor)
            ue_projectile_movement_launch(movement, ue_ref(type<SceneComponentRef>, sphere.handle), UE_VECTOR_ZERO, 0.0f)
        }
        return actor
    }

    [ue_function(BlueprintCallable)]
    def SetOverlap(actor : ActorRef; enabled : bool) : void {
        ue_component_find(type<StaticMeshComponentRef>, actor).SetGenerateOverlapEvents(enabled)
    }

    [ue_function(BlueprintCallable)]
    def UsePawnChannel(actor : ActorRef) : void {
        ue_component_find(type<StaticMeshComponentRef>, actor).SetCollisionObjectType(ECollisionChannel.ECC_Pawn)
    }
}
