options gen2
module rogue_eqs_alive_players public
require rogue_character public
require ue_behavior_tree public
require ue_api_world public

typedef EQSPlayerRef = UEObjectRef("rogue.RogueCharacter")

// URogueEnvQueryContext_AlivePlayers: every living player, not just player zero.
[ue_class(module_id="rogue", Blueprintable)]
class RogueEQSAlivePlayers : EQSContext {
    [ue_function(BlueprintEvent)]
    def const ProvideActorsSet(QuerierObject : ObjectRef; QuerierActor : ActorRef;
        @ue_out var ResultingActorsSet : array<ActorRef>&) : void {
        let kind = ue_class_loaded(type<EQSPlayerRef>, "/Game/DasRogue/BP_RogueCharacter.BP_RogueCharacter_C")
        let players <- ue_static(GameplayStatics.GetAllActorsOfClass, kind)
        var living : array<ActorRef>
        for (actor in players) {
            if (ue_ref(type<EQSPlayerRef>, actor.handle).IsAlive()) { push(living, ue_ref(type<ActorRef>, actor.handle)) }
        }
        ResultingActorsSet := living
    }
}
