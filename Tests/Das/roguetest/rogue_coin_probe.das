options gen2
module rogue_coin_probe public
require rogue_action_probe public
require rogue_coin_pickup_subsystem public
require rogue_ai_character public
require rogue_ai_controller public

typedef CoinAIControllerRef = UEObjectRef("rogue.RogueAIController")

[ue_class(module_id="roguetest", Blueprintable)]
class RogueCoinProbe : RogueActionProbe {
    settings = ue_properties(EditAnywhere, BlueprintReadWrite) {
        var CoinSystemClass : ObjectClass
    }

    [ue_function(BlueprintCallable)]
    def Coins() : RogueCoinPickupSubsystemRef {
        return ue_subsystem(type<RogueCoinPickupSubsystemRef>, self.CoinSystemClass)
    }

    [ue_function(BlueprintCallable)]
    def SetCollect(enabled : bool) : void { self.Coins().AutoCollect = enabled }

    [ue_function(BlueprintCallable)]
    def SetHealth(actor : ActorRef; value : float) : void {
        // Inject the wallet availability case without delivering terminal death events.
        let component = ue_component_find(type<RogueAttributeComponentRef>, actor)
        let attributes = component.GetAttributeSet()
        var bases := attributes.BaseValues
        bases["Attribute.Health"] = value
        attributes.BaseValues := bases
        attributes.Reconcile()
        component.Health = attributes.GetValue(ue_tag("Attribute.Health"))
    }

    [ue_function(BlueprintCallable)]
    def ConfigureEnemy(actor : ActorRef; data : RogueMonsterDataRef) : void {
        let enemy = ue_ref(type<RogueAICharacterRef>, actor.handle)
        enemy.MonsterData = data
        let controller = ue_ref(type<CoinAIControllerRef>, ue_ref(type<CharacterRef>, actor.handle).GetController().handle)
        if (ue_is_valid(controller)) { controller.BrainEnabled = false; controller.ForgetTarget() }
    }

    [ue_function(BlueprintCallable)]
    def InvalidNativeRemoval(id : int) : bool {
        var ids : array<int>
        push(ids,id)
        push(ids,-1)
        return ue_ism_remove_instances(self.Coins().WorldISM, ids)
    }

    [ue_function(BlueprintCallable)]
    def InstanceIndex(id : int) : int { return ue_ism_instance_index(self.Coins().WorldISM, id) }

    [ue_function(BlueprintCallable)]
    def RepeatDrop(actor : ActorRef) : void {
        let enemy = ue_ref(type<RogueAICharacterRef>, actor.handle)
        let action = enemy.ActionSystem.FindAction(ue_tag("Action.DropLoot"))
        if (ue_is_valid(action)) { action.StartAction() }
    }

    [ue_function(BlueprintCallable)]
    def RandomSequence(seed : int) : array<int> {
        var state = seed
        var result : array<int>
        for (index in range(6)) { push(result,ue_random_int(state,1,15)) }
        return <- result
    }

    [ue_function(BlueprintCallable)]
    def RandomValue(var seed : int&; low : int; high : int) : int {
        return ue_random_int(seed,low,high)
    }
}
