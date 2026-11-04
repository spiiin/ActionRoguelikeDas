options gen2
module rogue_barrel_probe public
require rogue_explosive_barrel public

[ue_class(module_id="roguetest", Blueprintable)]
class RogueBarrelProbe : Actor {
    @ue_component
    @RootComponent
    TargetMesh : StaticMeshComponentRef

    state = ue_properties(BlueprintReadWrite) { var DamageNotifications : int = 0 }

    defaults = ue_defaults() {
        self.TargetMesh.StaticMesh = ue_asset_default("/Engine/BasicShapes/Cube.Cube")
        self.TargetMesh.RelativeScale3D = ue_vector(0.3lf,0.3lf,0.3lf)
    }

    def BeginPlay() : void {
        self.SetActorTickEnabled(false)
        self.TargetMesh.SetCollisionProfileName(ue_name_value("BlockAllDynamic"), true)
    }

    [ue_event(source=self, name=OnTakeAnyDamage)]
    def OnDamage(damaged : ActorRef; amount : float; kind : ObjectRef; instigator : ObjectRef; source : ActorRef) : void {
        self.DamageNotifications += 1
    }

    [ue_function(BlueprintCallable)]
    def Spawn(kind : ActorClass; position : UEVector) : ActorRef {
        return ue_actor_spawn(type<ActorRef>, kind,
            ue_transform(position, UE_ROTATOR_ZERO, UE_VECTOR_ONE), default<ActorRef>, "AlwaysSpawn")
    }
}
