options gen2
module rogue_attribute_events public
require ue_native_gameplay public

[ue_multicast]
struct RogueHealthChanged {
    signature : function<(Instigator : ActorRef; NewHealth : float; Delta : float) : void>
}


[ue_multicast]
struct RogueAttributeChanged {
    signature : function<(Tag : GameplayTag; NewValue : float; OldValue : float; Instigator : ActorRef) : void>
}
