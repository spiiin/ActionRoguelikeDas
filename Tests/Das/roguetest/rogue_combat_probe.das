options gen2
require ue_vector_math public
require ue_native_gameplay

[ue_class(module_id="roguetest", Blueprintable)]
class CombatProbe : Actor {

    [ue_function(BlueprintCallable)]
    def Spawn(kind : ActorClass; position : UEVector; rotation : UERotator) : ActorRef {
        return ue_actor_spawn(type<ActorRef>, kind,
            ue_transform(position, rotation, UE_VECTOR_ONE), default<ActorRef>, "AlwaysSpawn")
    }
}
