options gen2
module rogue_action_blackhole public
require rogue_action_projectile_attack public

[ue_class(module_id="rogue", Blueprintable)]
class RogueActionBlackhole : RogueActionProjectileAttack {
    defaults = ue_defaults() {
        self.ProjectileClass = ue_class_default("/Game/DasRogue/Projectiles/BP_BlackholeAttackProjectile.BP_BlackholeAttackProjectile_C")
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override Setup() : void {
        Super.Setup()
        self.ActionName = ue_tag("Action.SecondaryAttack")
        var costs := self.ActivationCost
        if (length(costs) == 0) {
            costs["Attribute.Rage"] = 25.0f
            self.ActivationCost := costs
        }
    }
}
