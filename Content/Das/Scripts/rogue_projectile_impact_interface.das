options gen2
module rogue_projectile_impact_interface public
require ue_native_gameplay public

[ue_interface(module_id="rogue", BlueprintType)]
class RogueImpactHandler {

    [ue_function(BlueprintCallable, Category="Projectile")]
    def ApplyProjectileDamage(other : ActorRef) : bool {}
}
