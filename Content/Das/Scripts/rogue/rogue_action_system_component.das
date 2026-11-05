options gen2
module rogue_action_system_component public
require rogue_tags public
require rogue_action public
require rogue_action_events public
require rogue_attribute_component public
require math
require daslib/match
require daslib/linq
require daslib/linq_boost

let ROGUE_MAX_COIN_BALANCE : int64 = 9223372036854775807l

[ue_class(module_id="rogue", type_folder="/Game/DasRogue/Types", Blueprintable),
 ue_implements(interface="/Game/DasRogue/Types/RogueActionHost.RogueActionHost_C")]
class RogueActionSystemComponent : ActorComponent {

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Actions") {
        var DefaultAttributeSetClass : ObjectClass
        var DefaultActions : array<ObjectClass>
        var BaseMoveSpeed : float = 450.0f
    }

    state = ue_properties(BlueprintReadWrite) {
        // Reflected strong ownership: Outer and standalone script handles do not retain actions.
        var Actions : array<RogueActionRef>
        var ActiveGameplayTags : GameplayTagContainer
        // Live inspection views; AttributeSet is authoritative after initialization.
        var Resources : table<string; float>
        var MoveSpeedMultiplier : float = 1.0f
        var Enabled : bool = true
        var AttributeSet : RogueAttributeSetRef
        var AttributeBridge : RogueAttributeComponentRef
        // Currency is integral; generic combat attributes remain floating point.
        var Coins : int64 = 0l
    }

    events = ue_properties(BlueprintAssignable) {
        var OnAttributeChanged : RogueAttributeChanged
        var OnCoinsChanged : RogueCoinsChanged
        var OnActionAdded : RogueActionChanged
        var OnActionRemoved : RogueActionChanged
        var GameplayTagUpdated : RogueGameplayTagUpdated
    }

    // A reflected class reference loads and retains this dependency with the Blueprint.
    defaults = ue_defaults() {
        self.DefaultAttributeSetClass = ue_class_default("/Game/DasRogue/Attributes/BP_RoguePawnAttributeSet.BP_RoguePawnAttributeSet_C")
    }

    def BeginPlay() : void {
        self.Enabled = true
        self.Coins = 0l
        for (kind in self.DefaultActions) {
            if (ue_class_valid(kind)) {
                self.GrantAction(kind)
            }
        }
    }

    def EndPlay(reason : int) : void {
        self.Shutdown()
        clear(self.Actions)
        self.ActiveGameplayTags = ue_tags()
    }

    [ue_function(BlueprintCallable)]
    def GrantAction(kind : ObjectClass) : RogueActionRef {
        if (!self.Enabled || !ue_class_valid(kind)) { return default<RogueActionRef> }
        var actions := self.Actions
        let existing = _fold <| each(actions)._where(
            _.IsEffect() && ue_class_path(_.GrantedClass) == ue_class_path(kind)
        ).first_or_default(default<RogueActionRef>)
        if (ue_is_valid(existing)) {
            existing.IncrementStackSize()
            return existing
        }
        let action = ue_object_new(type<RogueActionRef>, kind, ue_ref(type<ObjectRef>, ue_self_object()))
        push(self.Actions, action)
        action.GrantedClass = kind
        action.Setup()
        if (action.IsEffect()) {
            if (!action.CanStart()) {
                self.RemoveAction(action)
                return default<RogueActionRef>
            }
            action.StartAction()
            if (!action.IsRunning()) {
                self.RemoveAction(action)
                return default<RogueActionRef>
            }
        }
        self.OnActionAdded.Broadcast(ue_ref(type<ObjectRef>, action.handle))
        return action
    }

    [ue_function(BlueprintCallable)]
    def FindAction(name : GameplayTag) : RogueActionRef {
        var actions := self.Actions
        return _fold <| each(actions)._where(ue_tag_matches(_.ActionName, name, true)).first_or_default(default<RogueActionRef>)
    }

    [ue_function(BlueprintCallable)]
    def StartAction(name : GameplayTag) : bool {
        if (!self.Enabled) { return false }
        let action = self.FindAction(name)
        if (!ue_is_valid(action) || !action.CanStart()) { return false }
        action.StartAction()
        return true
    }

    [ue_function(BlueprintCallable)]
    def StopAction(name : GameplayTag) : bool {
        let action = self.FindAction(name)
        if (!ue_is_valid(action) || !action.IsRunning()) { return false }
        action.StopAction()
        return true
    }

    [ue_function(BlueprintCallable)]
    def RemoveAction(removed : RogueActionRef) : bool {
        var next : array<RogueActionRef>
        var found = false
        for (action in self.Actions) {
            if (!found && ue_same_object(action, removed)) {
                found = true
            } else { push(next, action) }
        }
        if (!found) { return false }
        // Detach before callbacks: an effect also removes itself when stopped.
        self.Actions := next
        if (removed.IsRunning()) { removed.StopAction() }
        self.OnActionRemoved.Broadcast(ue_ref(type<ObjectRef>, removed.handle))
        return true
    }

    [ue_function(BlueprintCallable)]
    def AppendActiveTags(tags : GameplayTagContainer) : void {
        var active = self.ActiveGameplayTags
        for (name in ue_tags_names(tags)) { ue_tags_add(active, ue_tag(name)) }
        self.ActiveGameplayTags = active
        var actions := self.Actions
        for (action in actions) {
            if (action.IsRunning() && ue_tags_has_any(tags, action.BlockedTags)) { action.StopAction() }
        }
        for (name in ue_tags_names(tags)) { self.GameplayTagUpdated.Broadcast(ue_tag(name), 1) }
    }

    [ue_function(BlueprintCallable)]
    def RemoveActiveTags(tags : GameplayTagContainer) : void {
        var active = self.ActiveGameplayTags
        for (name in ue_tags_names(tags)) { ue_tags_remove(active, ue_tag(name)) }
        self.ActiveGameplayTags = active
        for (name in ue_tags_names(tags)) { self.GameplayTagUpdated.Broadcast(ue_tag(name), 0) }
    }

    [ue_function(BlueprintCallable)]
    def GetActiveTags() : GameplayTagContainer { return self.ActiveGameplayTags }

    [ue_function(BlueprintCallable)]
    def IsActionOwnerAlive() : bool { return self.Enabled }

    [ue_function(BlueprintPure)]
    def CanReceiveCoins(amount : int64) : bool {
        return self.Enabled && amount >= 0l && self.Coins >= 0l && self.Coins <= ROGUE_MAX_COIN_BALANCE - amount
    }

    [ue_function(BlueprintCallable)]
    def GrantCoins(amount : int64) : bool {
        if (!self.CanReceiveCoins(amount)) { return false }
        self.Coins += amount
        self.OnCoinsChanged.Broadcast(self.Coins)
        return true
    }

    def FindAttributeBridge() : RogueAttributeComponentRef {
        if (!ue_is_valid(self.AttributeBridge)) {
            self.AttributeBridge = ue_component_find(type<RogueAttributeComponentRef>, ue_self_actor())
        }
        return self.AttributeBridge
    }

    def AttachAttributeSet(attributes : RogueAttributeSetRef) : void {
        if (ue_same_object(self.AttributeSet, attributes)) { return }
        if (ue_is_valid(self.AttributeSet)) { self.AttributeSet.OnAttributeChanged -= self.HandleAttributeChanged }
        self.AttributeSet = attributes
        self.AttributeSet.OnAttributeChanged += self.HandleAttributeChanged
        self.RefreshAttributeViews()
    }

    [ue_function(BlueprintCallable)]
    def ConfigureAttributeSet(kind : ObjectClass) : bool {
        if (!ue_class_valid(kind)) { return false }
        let bridge = self.FindAttributeBridge()
        if (ue_is_valid(bridge)) {
            if (!bridge.ConfigureAttributeSet(kind)) { return false }
            self.AttachAttributeSet(bridge.GetAttributeSet())
        } else {
            let attributes = ue_object_new(type<RogueAttributeSetRef>, kind, ue_ref(type<ObjectRef>, ue_self_object()))
            self.AttachAttributeSet(attributes)
            attributes.InitializeAttributes()
        }
        return true
    }

    [ue_function(BlueprintCallable)]
    def GetAttributeSet() : RogueAttributeSetRef {
        let bridge = self.FindAttributeBridge()
        if (ue_is_valid(bridge) && ue_is_valid(bridge.AttributeSet) && !ue_same_object(self.AttributeSet, bridge.AttributeSet)) {
            self.AttachAttributeSet(bridge.AttributeSet)
        }
        if (!ue_is_valid(self.AttributeSet)) { self.ConfigureAttributeSet(self.DefaultAttributeSetClass) }
        return self.AttributeSet
    }

    def RefreshAttributeViews() : void {
        let attributes = self.AttributeSet
        if (attributes.HasAttribute(rogue_tag_move_speed())) {
            self.BaseMoveSpeed = attributes.GetBaseValue(rogue_tag_move_speed())
            self.MoveSpeedMultiplier = attributes.GetValue(rogue_tag_move_speed_multiplier())
        }
        var resources : table<string; float>
        var bases := attributes.BaseValues
        for (name in keys(bases)) { resources[name] = attributes.GetValue(ue_tag(name)) }
        self.Resources := resources
    }

    def HandleAttributeChanged(tag : GameplayTag; value : float; oldValue : float; instigator : ActorRef) : void {
        self.RefreshAttributeViews()
        self.OnAttributeChanged.Broadcast(tag, value, oldValue, instigator)
    }

    [ue_function(BlueprintCallable)]
    def GetAttributeValue(tag : GameplayTag) : float { return self.GetAttributeSet().GetValue(tag) }

    [ue_function(BlueprintCallable)]
    def ModifyAttribute(tag : GameplayTag; amount : float; kind : RogueAttributeModifyType) : bool {
        let bridge = self.FindAttributeBridge()
        self.GetAttributeSet()
        var changed = false
        if (ue_is_valid(bridge)) { changed = bridge.ModifyAttribute(tag, amount, kind, ue_self_actor()) }
        else { changed = self.AttributeSet.ModifyAttribute(tag, amount, kind, ue_self_actor()) }
        self.RefreshAttributeViews()
        return changed
    }

    // Actions consume/refund modifiers; health damage and pickups explicitly modify Base.
    [ue_function(BlueprintCallable)]
    def ApplyAttributeChange(tag : GameplayTag; delta : float) : void {
        self.ModifyAttribute(tag, delta, RogueAttributeModifyType.Modifier)
    }

    [ue_function(BlueprintCallable)]
    def SetBaseMoveSpeed(value : float) : void {
        self.ModifyAttribute(rogue_tag_move_speed(), value, RogueAttributeModifyType.OverrideBase)
    }

    def ApplyMoveSpeed() : void { self.GetAttributeSet().Reconcile() }

    [ue_function(BlueprintCallable)]
    def Shutdown() : void {
        self.Enabled = false
        var actions := self.Actions
        for (action in actions) {
            if (action.IsRunning()) {
                action.StopAction()
            }
        }
    }
}

typedef RogueActionSystemComponentRef = UEObjectRef("rogue.RogueActionSystemComponent")
