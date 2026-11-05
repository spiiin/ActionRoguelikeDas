options gen2
module rogue_health_widget_component public
require rogue_ui public
require rogue_attribute_component public
require rogue_effect_ui public

// Native UserWidget layout, with the original world-widget policy implemented in DAS.
[ue_class(module_id="rogue", Blueprintable)]
class RogueHealthWidgetComponent : ActorComponent {
    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Health widget") {
        var WidgetClass : UserWidgetClass
        var EffectClass : UserWidgetClass
        var AnchorOffset : UEVector = UE_VECTOR_ZERO
    }

    state = ue_properties(BlueprintReadWrite) {
        var Widget : UserWidgetRef
        var Attributes : RogueAttributeComponentRef
        var System : RogueActionSystemComponentRef
        var EffectActions : array<RogueActionRef>
        var EffectWidgets : array<UserWidgetRef>
        var NextEffectsUpdate : double = 0.0lf
        var EffectsCreated : int = 0
        var EffectsRemoved : int = 0
        var Player : PlayerControllerRef
        var WasDamaged : bool = false
        var Projected : bool = false
        var LastScreenPosition : UEVector2D
        var WidgetCreations : int = 0
        var PositionUpdates : int = 0
    }

    defaults = ue_defaults() {
        self.EffectClass = ue_class_default("/Game/DasRogue/UI/WBP_RogueEffect.WBP_RogueEffect_C")
    }

    def BeginPlay() : void {
        self.Attributes = ue_component_find(type<RogueAttributeComponentRef>, ue_self_actor())
        if (ue_is_valid(self.Attributes)) { self.Attributes.OnHealthChanged += self.OnHealthChanged }
        self.System = ue_component_find(type<RogueActionSystemComponentRef>, ue_self_actor())
        if (ue_is_valid(self.System)) {
            self.System.OnActionAdded += self.OnActionsChanged
            self.System.OnActionRemoved += self.OnActionsChanged
        }
        self.SetComponentTickEnabled(false)
    }

    [ue_function(BlueprintCallable)]
    def Configure(kind : UEClassHandle) : void {
        self.ClearWidget()
        if (!ue_class_valid(kind)) { self.WidgetClass = default<UserWidgetClass>; return }
        self.WidgetClass = ue_class_cast(type<UserWidgetClass>, kind)
    }

    def OnHealthChanged(instigator : ActorRef; health, delta : float) : void {
        if (health <= 0.0f) { self.ClearWidget(); return }
        if (delta < 0.0f) { self.WasDamaged = true }
        if (self.WasDamaged) { self.EnsureWidget(); self.RefreshHealth() }
    }

    def EnsureWidget() : void {
        if (ue_is_valid(self.Widget) || !ue_class_valid(self.WidgetClass)) { return }
        self.Player = ue_ref(type<PlayerControllerRef>, ue_static(GameplayStatics.GetPlayerController, 0).handle)
        if (!ue_is_valid(self.Player) || !self.Player.IsLocalController()) { return }
        self.Widget = ue_widget_create(self.WidgetClass, self.Player)
        verify(ue_widget_show(self.Widget), "Cannot show the monster health widget")
        let widget = rogue_ui_widget(self.Widget)
        ue_user_widget_SetAlignmentInViewport(widget, ue_vector2d(0.5lf, 1.0lf))
        ue_user_widget_SetDesiredSizeInViewport(widget, ue_vector2d(244.0lf, 40.0lf))
        self.WidgetCreations += 1
        self.SetComponentTickEnabled(true)
        self.UpdatePosition()
        self.RefreshEffects()
    }

    [ue_function(BlueprintCallable)]
    def RefreshHealth() : void {
        if (!ue_is_valid(self.Widget) || !ue_is_valid(self.Attributes)) { return }
        let view = ue_widget_view(type<RogueHealthView>, self.Widget)
        ue_progress_SetPercent(view.HealthBar, rogue_ui_fraction(self.Attributes.Health, self.Attributes.HealthMax))
        ue_widget_set_text(view.HealthText, ue_text_invariant("{int(self.Attributes.Health)} / {int(self.Attributes.HealthMax)}"))
    }

    def OnActionsChanged(action : ObjectRef) : void { self.RefreshEffects() }

    [ue_function(BlueprintCallable)]
    def RefreshEffects() : void {
        if (!ue_is_valid(self.Widget) || !ue_class_valid(self.EffectClass)) { return }
        // Shutdown broadcasts removals before this component's EndPlay can run.
        if (!ue_is_valid(self.System) || !self.System.Enabled) { return }
        let view = ue_widget_view(type<RogueEnemyEffectsView>, self.Widget)
        var actions := self.EffectActions
        var widgets := self.EffectWidgets
        let counts = rogue_ui_refresh_effects(self.System, self.Player, self.EffectClass, ue_ref(type<PanelWidget>, view.Effects.handle), actions, widgets)
        self.EffectActions := actions
        self.EffectWidgets := widgets
        self.EffectsCreated += counts.x
        self.EffectsRemoved += counts.y
    }

    def ClearEffects() : void {
        var actions := self.EffectActions
        var widgets := self.EffectWidgets
        self.EffectsRemoved += rogue_ui_clear_effects(actions, widgets)
        self.EffectActions := actions
        self.EffectWidgets := widgets
    }

    def Tick(delta : float) : void {
        self.UpdatePosition()
        if (ue_world_seconds() >= self.NextEffectsUpdate) {
            self.NextEffectsUpdate = ue_world_seconds() + 0.1lf
            self.RefreshEffects()
        }
    }

    [ue_function(BlueprintCallable)]
    def UpdatePosition() : void {
        if (!ue_is_valid(self.Widget) || !ue_is_valid(self.Player)) { return }
        let location = ue_self_actor().K2_GetActorLocation() + self.AnchorOffset
        let projection = ue_static(WidgetLayoutLibrary.ProjectWorldLocationToWidgetPosition, self.Player, location, true)
        self.Projected = projection.out_returnvalue
        rogue_ui_visibility(self.Widget, self.Projected)
        if (self.Projected) {
            self.LastScreenPosition = projection.out_screenposition
            // Projection has removed DPI already; false prevents applying the correction twice.
            ue_user_widget_SetPositionInViewport(rogue_ui_widget(self.Widget), self.LastScreenPosition, false)
            self.PositionUpdates += 1
        }
    }

    [ue_function(BlueprintCallable)]
    def ClearWidget() : void {
        self.ClearEffects()
        if (ue_is_valid(self.Widget)) { ue_widget_remove(self.Widget) }
        self.Widget = default<UserWidgetRef>
        self.Projected = false
        self.SetComponentTickEnabled(false)
    }

    def EndPlay(reason : int) : void {
        if (ue_is_valid(self.Attributes)) { self.Attributes.OnHealthChanged -= self.OnHealthChanged }
        if (ue_is_valid(self.System)) {
            self.System.OnActionAdded -= self.OnActionsChanged
            self.System.OnActionRemoved -= self.OnActionsChanged
        }
        self.ClearEffects()
        // Tick is already stopped by Unreal during EndPlay.
        if (ue_is_valid(self.Widget)) { ue_widget_remove(self.Widget) }
        self.Widget = default<UserWidgetRef>
        self.Projected = false
    }
}

typedef RogueHealthWidgetComponentRef = UEObjectRef("rogue.RogueHealthWidgetComponent")
