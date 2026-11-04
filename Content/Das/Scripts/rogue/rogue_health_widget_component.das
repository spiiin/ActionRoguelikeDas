options gen2
module rogue_health_widget_component public
require rogue_ui public
require rogue_attribute_component public

// Native UserWidget layout, with the original world-widget policy implemented in DAS.
[ue_class(module_id="rogue", Blueprintable)]
class RogueHealthWidgetComponent : ActorComponent {
    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Health widget") {
        var WidgetClass : UserWidgetClass
        var AnchorOffset : UEVector = UE_VECTOR_ZERO
    }

    state = ue_properties(BlueprintReadWrite) {
        var Widget : UserWidgetRef
        var Attributes : RogueAttributeComponentRef
        var Player : PlayerControllerRef
        var WasDamaged : bool = false
        var Projected : bool = false
        var LastScreenPosition : UEVector2D
        var WidgetCreations : int = 0
        var PositionUpdates : int = 0
    }

    def BeginPlay() : void {
        self.Attributes = ue_component_find(type<RogueAttributeComponentRef>, ue_self_actor())
        if (ue_is_valid(self.Attributes)) { self.Attributes.OnHealthChanged += self.OnHealthChanged }
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
        ue_user_widget_SetDesiredSizeInViewport(widget, ue_vector2d(156.0lf, 40.0lf))
        self.WidgetCreations += 1
        self.SetComponentTickEnabled(true)
        self.UpdatePosition()
    }

    [ue_function(BlueprintCallable)]
    def RefreshHealth() : void {
        if (!ue_is_valid(self.Widget) || !ue_is_valid(self.Attributes)) { return }
        let view = ue_widget_view(type<RogueHealthView>, self.Widget)
        ue_progress_SetPercent(view.HealthBar, rogue_ui_fraction(self.Attributes.Health, self.Attributes.HealthMax))
        ue_widget_set_text(view.HealthText, ue_text_invariant("{int(self.Attributes.Health)} / {int(self.Attributes.HealthMax)}"))
    }

    def Tick(delta : float) : void { self.UpdatePosition() }

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
        if (ue_is_valid(self.Widget)) { ue_widget_remove(self.Widget) }
        self.Widget = default<UserWidgetRef>
        self.Projected = false
        self.SetComponentTickEnabled(false)
    }

    def EndPlay(reason : int) : void {
        if (ue_is_valid(self.Attributes)) { self.Attributes.OnHealthChanged -= self.OnHealthChanged }
        self.ClearWidget()
    }
}

typedef RogueHealthWidgetComponentRef = UEObjectRef("rogue.RogueHealthWidgetComponent")
