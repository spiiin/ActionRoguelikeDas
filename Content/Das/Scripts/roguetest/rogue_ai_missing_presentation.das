options gen2
module rogue_ai_missing_presentation public
require rogue_ai_character public

[ue_class(module_id="roguetest", Blueprintable)]
class RogueAIMissingPresentation : RogueAICharacter {
    defaults = ue_defaults() {
        self.PresentationProfilePath = "/Game/DoesNotExist/MinionProfile.MinionProfile"
    }
}
