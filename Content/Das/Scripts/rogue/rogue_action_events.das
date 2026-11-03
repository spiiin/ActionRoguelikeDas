options gen2
module rogue_action_events public
require ue_native_gameplay public

[ue_multicast]
struct RogueActionChanged { signature : function<(Action : ObjectRef) : void> }

[ue_multicast]
struct RogueGameplayTagUpdated { signature : function<(Tag : GameplayTag; NewCount : int) : void> }

[ue_multicast]
struct RogueCoinsChanged { signature : function<(Balance : int64) : void> }
