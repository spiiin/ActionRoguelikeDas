options gen2
module rogue_magic_projectile public
require rogue_projectile public
require ue_native_gameplay public
require rogue_effect_helpers public

// Damage slice of ARogueProjectileMagic; AI noise/impulse/action effects follow later.
[ue_class(module_id="rogue", Blueprintable)]
class RogueMagicProjectile : RogueProjectile {

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Projectile") {
        var AttackDamage : float = 25.0f
        var EffectOnHit : ObjectClass
    }

    defaults = ue_defaults() { self.InitialLifeSpan = 8.0f }

    [ue_function(BlueprintEvent, Category="Projectile")]
    def override ApplyProjectileDamage(other : ActorRef) : bool {
        if (!ue_object_valid(other.handle) || ue_same_object(other, self.Instigator)) { return false }
        var controller = default<PlayerControllerRef>
        if (ue_object_valid(self.Instigator.handle)) { controller = ue_pawn_controller(self.Instigator) }
        var damaged = false
        if (self.AttackDamage > 0.0f) { damaged = ue_apply_damage(other, self.AttackDamage, ue_self_actor(), controller) > 0.0f }
        // Damage notifications are queued during managed hit dispatch. Any
        // lethal notification will shut down the target and remove this effect.
        rogue_apply_hit_effect(other, self.EffectOnHit)
        return damaged
    }
}
