options gen2
module rogue_ai_presentation_probe public
require rogue_action_probe public
require rogue_ai_controller public

typedef PresentationControllerRef = UEObjectRef("rogue.RogueAIController")

[ue_class(module_id="roguetest", Blueprintable)]
class RogueAIPresentationProbe : RogueActionProbe {
    [ue_function(BlueprintCallable)]
    def FreezeBrain(enemy : RogueAICharacterRef; target : ActorRef) : void {
        let pawn = ue_ref(type<NativePawnRef>, enemy.handle)
        let controller = ue_ref(type<PresentationControllerRef>, pawn.GetController().handle)
        controller.BrainEnabled = false
        controller.ForgetTarget()
        enemy.Target = target
    }
}
