options gen2
module rogue_action_teleport public
require rogue_action_projectile_attack public

[ue_class(module_id="rogue", Blueprintable)]
class RogueActionTeleport : RogueActionProjectileAttack {
    defaults = ue_defaults() {
        self.ProjectileClass = ue_class_default("/Game/DasRogue/Projectiles/BP_TeleportDemo.BP_TeleportDemo_C")
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override Setup() : void {
        Super.Setup()
        self.ActionName = ue_tag("Action.SpecialAttack")
    }
}
