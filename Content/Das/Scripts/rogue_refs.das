options gen2
module rogue_refs public
require ue_dsl public

[ue_object_ref(script="rogue_interaction_component.das", type= "RogueInteractionComponent")]
struct RogueInteractionComponentRef { handle : UObjectHandle }
