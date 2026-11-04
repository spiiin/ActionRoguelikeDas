options gen2
module rogue_hud_component public
require rogue_ui public
require rogue_action_effect public

typedef RogueActionEffectRef = UEObjectRef("rogue.RogueActionEffect")

typedef RogueEffectTexture = $UESoftObject<ue_api_umg_input::Texture2D>

// The Widget Blueprint owns only layout. State, subscriptions and lifetime are DAS.
[ue_class(module_id="rogue", Blueprintable)]
class RogueHUDComponent : ActorComponent {
    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="HUD") {
        var HUDClass : UserWidgetClass
        var EffectClass : UserWidgetClass
        var RageMaximum : float = 100.0f
    }

    state = ue_properties(BlueprintReadWrite) {
        var HUD : UserWidgetRef
        var Pawn : ActorRef
        var System : RogueActionSystemComponentRef
        var EffectActions : array<RogueActionRef>
        var EffectWidgets : array<UserWidgetRef>
        var NextEffectsUpdate : double = 0.0lf
        var VitalsUpdates : int = 0
        var PawnBindings : int = 0
        var EffectsCreated : int = 0
        var EffectsRemoved : int = 0
    }

    defaults = ue_defaults() {
        self.HUDClass = ue_class_default("/Game/DasRogue/UI/WBP_RogueHUD.WBP_RogueHUD_C")
        self.EffectClass = ue_class_default("/Game/DasRogue/UI/WBP_RogueEffect.WBP_RogueEffect_C")
    }

    def Tick(delta : float) : void {
        let player = ue_ref(type<PlayerControllerRef>, ue_component_owner(ue_self_object()))
        if (!player.IsLocalController() || !ue_player_controls_ready(player)) { return }
        if (!ue_widget_visible(self.HUD)) {
            self.ClearHUD()
            if (!ue_class_valid(self.HUDClass)) { return }
            self.HUD = ue_widget_create(self.HUDClass, player)
            verify(ue_widget_show(self.HUD), "Cannot show the local player HUD")
            rogue_ui_visibility(self.HUD, true)
            self.RefreshVitals()
        }
        let pawn = ue_ref(type<ActorRef>, player.K2_GetPawn().handle)
        if (ue_is_valid(pawn) != ue_is_valid(self.Pawn) || (ue_is_valid(pawn) && !ue_same_object(pawn, self.Pawn))) {
            self.BindPawn(pawn)
        }
        if (ue_world_seconds() >= self.NextEffectsUpdate) {
            self.NextEffectsUpdate = ue_world_seconds() + 0.1lf
            self.RefreshEffects()
        }
    }

    [ue_function(BlueprintCallable)]
    def BindPawn(pawn : ActorRef) : void {
        self.UnbindPawn()
        self.Pawn = pawn
        if (ue_is_valid(pawn)) { self.System = ue_component_find(type<RogueActionSystemComponentRef>, pawn) }
        if (ue_is_valid(self.System)) {
            self.System.OnAttributeChanged += self.OnAttributeChanged
            self.System.OnCoinsChanged += self.OnCoinsChanged
            self.System.OnActionAdded += self.OnActionsChanged
            self.System.OnActionRemoved += self.OnActionsChanged
            self.PawnBindings += 1
        }
        self.RefreshVitals()
        self.RefreshEffects()
    }

    def UnbindPawn() : void {
        if (ue_is_valid(self.System)) {
            self.System.OnAttributeChanged -= self.OnAttributeChanged
            self.System.OnCoinsChanged -= self.OnCoinsChanged
            self.System.OnActionAdded -= self.OnActionsChanged
            self.System.OnActionRemoved -= self.OnActionsChanged
        }
        self.System = default<RogueActionSystemComponentRef>
        self.Pawn = default<ActorRef>
        self.ClearEffects()
    }

    def OnAttributeChanged(tag : GameplayTag; value, previous : float; instigator : ActorRef) : void {
        let name = ue_tag_name(tag)
        if (name == "Attribute.Health" || name == "Attribute.HealthMax" || name == "Attribute.Rage") { self.RefreshVitals() }
    }

    def OnCoinsChanged(balance : int64) : void { self.RefreshVitals() }

    def OnActionsChanged(action : ObjectRef) : void { self.RefreshEffects() }

    [ue_function(BlueprintCallable)]
    def RefreshVitals() : void {
        if (!ue_widget_visible(self.HUD)) { return }
        let view = ue_widget_view(type<RogueHUDView>, self.HUD)
        let bound = ue_is_valid(self.System)
        let health = bound ? self.System.GetAttributeValue(ue_tag("Attribute.Health")) : 0.0f
        let maximum = bound ? self.System.GetAttributeValue(ue_tag("Attribute.HealthMax")) : 0.0f
        let rage = bound ? self.System.GetAttributeValue(ue_tag("Attribute.Rage")) : 0.0f
        let coins = bound ? self.System.Coins : 0l
        ue_progress_SetPercent(view.HealthBar, rogue_ui_fraction(health, maximum))
        ue_progress_SetPercent(view.RageBar, rogue_ui_fraction(rage, self.RageMaximum))
        ue_widget_set_text(view.HealthText, ue_text_invariant("HP  {int(health)} / {int(maximum)}"))
        ue_widget_set_text(view.RageText, ue_text_invariant("RAGE  {int(rage)} / {int(self.RageMaximum)}"))
        ue_widget_set_text(view.CoinsText, ue_text_invariant("COINS  {coins}"))
        self.VitalsUpdates += 1
    }

    [ue_function(BlueprintCallable)]
    def RefreshEffects() : void {
        if (!ue_widget_visible(self.HUD)) { return }
        if (!ue_class_valid(self.EffectClass)) { self.ClearEffects(); return }
        let view = ue_widget_view(type<RogueHUDView>, self.HUD)
        var active : array<RogueActionRef>
        if (ue_is_valid(self.System)) {
            for (action in self.System.Actions) {
                if (ue_is_valid(action) && action.IsEffect() && action.IsRunning()) { push(active, action) }
            }
        }
        var nextWidgets : array<UserWidgetRef>
        var oldActions := self.EffectActions
        var oldWidgets := self.EffectWidgets
        for (i in range(length(oldActions))) {
            var retained = false
            for (action in active) { if (ue_same_object(action, oldActions[i])) { retained = true; break } }
            if (!retained && ue_is_valid(oldWidgets[i])) {
                ue_widget_remove(oldWidgets[i])
                self.EffectsRemoved += 1
            }
        }
        for (action in active) {
            var item : UserWidgetRef
            for (i in range(length(oldActions))) {
                if (ue_same_object(action, oldActions[i])) { item = oldWidgets[i]; break }
            }
            if (!ue_is_valid(item)) {
                if (!ue_class_valid(self.EffectClass)) { continue }
                let player = ue_ref(type<PlayerControllerRef>, ue_component_owner(ue_self_object()))
                item = ue_widget_create(self.EffectClass, player)
                ue_panel_AddChild(ue_ref(type<PanelWidget>, view.Effects.handle), ue_ref(type<Widget>, item.handle))
                let iconView = ue_widget_view(type<RogueEffectView>, item)
                let icon = ue_soft(type<RogueEffectTexture>, action.IconPath)
                ue_image_SetBrushFromSoftTexture(iconView.Icon, icon, false)
                self.EffectsCreated += 1
            }
            let effectView = ue_widget_view(type<RogueEffectView>, item)
            let effect = ue_ref(type<RogueActionEffectRef>, action.handle)
            let effectName = action.DisplayName != "" ? action.DisplayName : ue_tag_name(action.ActionName)
            ue_widget_set_text(effectView.EffectName, ue_text_invariant(effectName))
            let remaining = effect.Duration > 0.0f ? max(0, int(ceil(effect.GetDurationRemaining()))) : -1
            let duration = remaining >= 0 ? "{remaining}s" : ""
            ue_widget_set_text(effectView.Details, ue_text_invariant("x{effect.StackCount}  {duration}"))
            push(nextWidgets, item)
        }
        // Only retain entries for widgets actually created; the normal configured class covers all entries.
        self.EffectActions := active
        self.EffectWidgets := nextWidgets
    }

    def ClearEffects() : void {
        for (widget in self.EffectWidgets) {
            if (ue_is_valid(widget)) { ue_widget_remove(widget); self.EffectsRemoved += 1 }
        }
        var actions : array<RogueActionRef>
        var widgets : array<UserWidgetRef>
        self.EffectActions := actions
        self.EffectWidgets := widgets
    }

    def ClearHUD() : void {
        self.ClearEffects()
        if (ue_is_valid(self.HUD)) { ue_widget_remove(self.HUD) }
        self.HUD = default<UserWidgetRef>
    }

    def EndPlay(reason : int) : void { self.UnbindPawn(); self.ClearHUD() }
}

typedef RogueHUDComponentRef = UEObjectRef("rogue.RogueHUDComponent")
