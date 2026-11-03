options gen2
module rogue_ai_projectile_attack public
require rogue_action_projectile_attack public
require rogue_ai_character public

// Original RogueBTTask_RangedAttack aims at TargetActor rather than the player camera.
[ue_class(module_id="rogue", Blueprintable)]
class RogueAIProjectileAttack : RogueActionProjectileAttack {
    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override GetAimPoint() : UEVector {
        let enemy = ue_ref(type<RogueAICharacterRef>,self.GetPawn().handle)
        if (ue_is_valid(enemy.Target)) { return enemy.Target.K2_GetActorLocation() }
        return ue_ref(type<ActorRef>,enemy.handle).K2_GetActorLocation()
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override GetAimRotation() : UERotator {
        let origin = ue_ref(type<ActorRef>,self.GetPawn().handle).K2_GetActorLocation()
        return ue_direction_rotation(self.GetAimPoint()-origin)
    }
}
