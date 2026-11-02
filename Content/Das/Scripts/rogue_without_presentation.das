options gen2
require rogue_character public

[ue_class(module_id="roguetest", Blueprintable)]
class RogueWithoutPresentation : RogueCharacter {
    defaults = ue_defaults() { self.UseExternalPresentation = false }
}

