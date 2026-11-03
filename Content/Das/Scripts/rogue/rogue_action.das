options gen2
module rogue_action public
require rogue_action_host_interface public
require math
require ue_result public

// Script-only diagnostic; Blueprint's CanStart contract remains bool.
enum RogueActionStartFailure {
    AlreadyRunning
    MissingHost
    InactiveOwner
    Cooldown
    BlockedTags
    InsufficientResource
}

// First action-system slice of Tom Looman's ActionRoguelike, commit 992f860.
// Publication permission and redistribution license are pending.
[ue_class(module_id="rogue", Blueprintable)]
class RogueAction : ScriptObject {

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Actions") {
        var ActionName : GameplayTag
        var GrantTags : GameplayTagContainer
        var BlockedTags : GameplayTagContainer
        var CooldownTime : float = 0.0f
        // Keys are registered GameplayTag names; values are required resource amounts.
        var ActivationCost : table<string; float>
    }

    state = ue_properties(BlueprintReadWrite) {
        var GrantedClass : ObjectClass
        var Host : RogueActionHostRef
        var bIsRunning : bool = false
        var CooldownUntil : double = 0.0lf
        var Starts : int = 0
        var Stops : int = 0
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def Setup() : void {
        self.Host = ue_ref(type<RogueActionHostRef>, ue_object_outer(ue_self_object()))
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def IsEffect() : bool { return false }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def IncrementStackSize() : void {}

    [ue_function(BlueprintCallable)]
    def GetOwningComponent() : RogueActionHostRef { return self.Host }

    [ue_function(BlueprintPure)]
    def IsRunning() : bool { return self.bIsRunning }

    [ue_function(BlueprintPure)]
    def GetCooldownTimeRemaining() : double {
        return max(0.0lf, self.CooldownUntil - ue_world_seconds())
    }

    def CheckCanStart() : Result<bool; RogueActionStartFailure> {
        ue_require(!self.bIsRunning, RogueActionStartFailure.AlreadyRunning) |> ue_try
        ue_require(ue_object_valid(self.Host.handle), RogueActionStartFailure.MissingHost) |> ue_try
        ue_require(self.Host.IsActionOwnerAlive(), RogueActionStartFailure.InactiveOwner) |> ue_try
        ue_require(!(self.GetCooldownTimeRemaining() > 0.0lf), RogueActionStartFailure.Cooldown) |> ue_try
        ue_require(!ue_tags_has_any(self.Host.GetActiveTags(), self.BlockedTags), RogueActionStartFailure.BlockedTags) |> ue_try
        var costs := self.ActivationCost
        for (name, value in keys(costs), values(costs)) {
            ue_require(!(self.Host.GetAttributeValue(ue_tag(name)) < value), RogueActionStartFailure.InsufficientResource) |> ue_try
        }
        return ok(true, type<RogueActionStartFailure>)
    }

    [ue_function(BlueprintPure)]
    def CanStart() : bool { return is_ok(self.CheckCanStart()) }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def StartAction() : void {
        self.Host.AppendActiveTags(self.GrantTags)
        var costs := self.ActivationCost
        for (name, value in keys(costs), values(costs)) {
            self.Host.ApplyAttributeChange(ue_tag(name), -value)
        }
        self.bIsRunning = true
        self.Starts += 1
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def StopAction() : void {
        self.bIsRunning = false
        self.CooldownUntil = 0.0lf
        // Shutdown marks the host inactive before stopping its actions. A world
        // being torn down has no gameplay clock and needs no future cooldown.
        if (self.CooldownTime > 0.0f && ue_is_valid(self.Host) && self.Host.IsActionOwnerAlive()) {
            self.CooldownUntil = ue_world_seconds() + double(self.CooldownTime)
        }
        if (ue_is_valid(self.Host)) { self.Host.RemoveActiveTags(self.GrantTags) }
        self.Stops += 1
    }
}

typedef RogueActionRef = UEObjectRef("rogue.RogueAction")
