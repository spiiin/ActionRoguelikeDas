options gen2
module rogue_projectile_impact_interface public
require ue_projectile_components public

[ue_interface(module_id="rogue", BlueprintType)]
class RogueImpactHandler {

    [ue_function(BlueprintCallable, Category="Projectile")]
    def HandleImpact(other : ActorRef; hit : CollisionHit) : bool {}

    [ue_function(BlueprintCallable, Category="Projectile")]
    def ApplyProjectileDamage(other : ActorRef; hit : CollisionHit) : bool {}
}

typedef RogueImpactHandlerRef = UEInterfaceRef("rogue.RogueImpactHandler")
