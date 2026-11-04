options gen2
module rogue_behavior_minion public
require rogue_ai_character public

[ue_class(module_id="roguedemo", Blueprintable)]
class RogueBehaviorMinion : RogueAICharacter {
    defaults=ue_defaults() {
        self.AIControllerClass=ue_class_default("/Game/DasRogue/AI/BP_RogueBehaviorController.BP_RogueBehaviorController_C")
    }
}

typedef RogueBehaviorMinionRef=UEObjectRef("roguedemo.RogueBehaviorMinion")
