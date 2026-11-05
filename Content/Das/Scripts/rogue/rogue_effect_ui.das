options gen2
module rogue_effect_ui public
require rogue_ui public
require rogue_action_effect public

typedef RogueUIActionEffectRef = UEObjectRef("rogue.RogueActionEffect")
typedef RogueUIEffectTexture = $UESoftObject<ue_api_umg_input::Texture2D>

// Same fallback as the course EffectSlot_WBP; optional and loaded asynchronously.
let ROGUE_DEFAULT_EFFECT_ICON = "/Game/ExampleContent/UI/Texture/T_UI_Icon_Settings01.T_UI_Icon_Settings01"

typedef RogueEnemyEffectsBoxRef = UENativeObjectRef("/Script/UMG.HorizontalBox")

[ue_widget_layout]
struct RogueEnemyEffectsView {
    Effects : RogueEnemyEffectsBoxRef
}

// The component retains both arrays as reflected strong references.
// x counts created rows, y counts removed rows.
def rogue_ui_refresh_effects(system : RogueActionSystemComponentRef; player : PlayerControllerRef;
    kind : UserWidgetClass; panel : PanelWidget;
    var actions : array<RogueActionRef>&; var widgets : array<UserWidgetRef>&) : int2 {
    var counts = int2(0)
    var active : array<RogueActionRef>
    if (ue_is_valid(system)) {
        for (action in system.Actions) {
            if (ue_is_valid(action) && action.IsEffect() && action.IsRunning()) { push(active, action) }
        }
    }
    var nextActions : array<RogueActionRef>
    var nextWidgets : array<UserWidgetRef>
    var oldActions := actions
    var oldWidgets := widgets
    for (i in range(length(oldActions))) {
        var retained = false
        for (action in active) { if (ue_same_object(action, oldActions[i])) { retained = true; break } }
        if (!retained && ue_is_valid(oldWidgets[i])) {
            ue_widget_remove(oldWidgets[i])
            counts.y += 1
        }
    }
    for (action in active) {
        var item : UserWidgetRef
        for (i in range(length(oldActions))) {
            if (ue_same_object(action, oldActions[i])) { item = oldWidgets[i]; break }
        }
        if (!ue_is_valid(item)) {
            if (!ue_class_valid(kind)) { continue }
            item = ue_widget_create(kind, player)
            if (!ue_is_valid(item)) { continue }
            ue_panel_AddChild(ue_ref(type<PanelWidget>, panel.handle), ue_ref(type<Widget>, item.handle))
            let iconView = ue_widget_view(type<RogueEffectView>, item)
            let iconPath = action.IconPath != "" ? action.IconPath : ROGUE_DEFAULT_EFFECT_ICON
            let icon = ue_soft(type<RogueUIEffectTexture>, iconPath)
            ue_image_SetBrushFromSoftTexture(iconView.Icon, icon, false)
            ue_widget_SetVisibility(ue_ref(type<Widget>, iconView.Icon.handle), E_ESlateVisibility_d128c9c0.v_HitTestInvisible)
            counts.x += 1
        }
        let effectView = ue_widget_view(type<RogueEffectView>, item)
        let effect = ue_ref(type<RogueUIActionEffectRef>, action.handle)
        let effectName = action.DisplayName != "" ? action.DisplayName : ue_tag_name(action.ActionName)
        ue_widget_set_text(effectView.EffectName, ue_text_invariant(effectName))
        let remaining = effect.Duration > 0.0f ? max(0, int(ceil(effect.GetDurationRemaining()))) : -1
        let duration = remaining >= 0 ? "{remaining}s" : ""
        ue_widget_set_text(effectView.Details, ue_text_invariant("x{effect.StackCount}  {duration}"))
        ue_widget_SetToolTipText(ue_ref(type<Widget>, item.handle), ue_text_invariant("{effectName}  x{effect.StackCount}  {duration}"))
        push(nextActions, action)
        push(nextWidgets, item)
    }
    actions := nextActions
    widgets := nextWidgets
    return counts
}

def rogue_ui_clear_effects(var actions : array<RogueActionRef>&; var widgets : array<UserWidgetRef>&) : int {
    var removed = 0
    for (widget in widgets) {
        if (ue_is_valid(widget)) { ue_widget_remove(widget); removed += 1 }
    }
    clear(actions)
    clear(widgets)
    return removed
}
