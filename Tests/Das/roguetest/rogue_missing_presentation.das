options gen2
require rogue_character public

[ue_class(module_id="roguetest", Blueprintable)]
class RogueMissingPresentation : RogueCharacter {
    defaults = ue_defaults() {
        self.PresentationProfilePath = "/Game/DoesNotExist/Optional.Optional"
    }
}
