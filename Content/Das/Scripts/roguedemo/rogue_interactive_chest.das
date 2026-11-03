options gen2
require rogue_item_chest

// Interactive sample: inherits the chest behavior without any demo timer.
[ue_class(module_id="roguedemo", Blueprintable)]
class RogueInteractiveChest : RogueItemChest {}
