options gen2
module rogue_action_refs public
require rogue_action_host_refs public
[ue_object_ref(script="rogue_action.das", type= "RogueAction")]
struct RogueActionRef { handle : UObjectHandle }
