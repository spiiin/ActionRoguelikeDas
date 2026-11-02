options gen2
module rogue_magic_projectile public
require rogue_projectile public
require ue_native_gameplay public
require rogue_effect_helpers public

// Damage slice of ARogueProjectileMagic; AI noise/impulse/action effects follow later.
[ue_class(module_id="rogue", Blueprintable)]
class RogueMagicProjectile : RogueProjectile {
    // The hit implementation now includes point damage, noise, impulse and effects.

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Projectile") {
        var AttackDamage : float = 25.0f
        var ImpulseIntensity : float = 200000.0f
        var NoiseLoudness : float = 1.0f
        var EffectOnHit : ObjectClass
    }

    defaults = ue_defaults() { self.InitialLifeSpan = 8.0f }

    [ue_function(BlueprintEvent, Category="Projectile")]
    def override ApplyProjectileDamage(other : ActorRef; hit : CollisionHit) : bool {
        if (!ue_object_valid(other.handle) || ue_same_object(other, self.Instigator)) { return false }
        var controller = default<PlayerControllerRef>
        if (ue_object_valid(self.Instigator.handle)) { controller = ue_pawn_controller(self.Instigator) }
        let direction = ue_self_actor().GetActorForwardVector()
        if (self.NoiseLoudness > 0.0f) {
            ue_report_noise(ue_self_actor().K2_GetActorLocation(), self.NoiseLoudness, self.Instigator)
        }
        var damaged = false
        if (self.AttackDamage > 0.0f) { damaged = ue_apply_point_damage(other, self.AttackDamage, direction, hit, ue_self_actor(), controller) > 0.0f }
        let component = TraceComponentRef_from(hit.Component.handle)
        if (ue_is_valid(component) && self.ImpulseIntensity > 0.0f && component.IsSimulatingPhysics(hit.BoneName)) {
            component.AddImpulseAtLocation(direction * double(self.ImpulseIntensity), hit.Location, hit.BoneName)
        }
        // Damage notifications are queued during managed hit dispatch. Any
        // lethal notification will shut down the target and remove this effect.
        rogue_apply_hit_effect(other, self.EffectOnHit)
        return damaged
    }
}
