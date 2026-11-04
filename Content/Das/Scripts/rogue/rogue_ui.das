options gen2
module rogue_ui public
require ue_native_gameplay public
require ue_api_umg_input public
require ue_api_world public
require ue_vector_math public
require math public

typedef RogueEffectsBoxRef = UENativeObjectRef("/Script/UMG.VerticalBox")

[ue_widget_layout]
struct RogueHUDView {
    HealthBar : ProgressBar
    HealthText : TextBlockRef
    RageBar : ProgressBar
    RageText : TextBlockRef
    CoinsText : TextBlockRef
    Effects : RogueEffectsBoxRef
}

[ue_widget_layout]
struct RogueHealthView {
    HealthBar : ProgressBar
    HealthText : TextBlockRef
}

[ue_widget_layout]
struct RogueEffectView {
    Icon : Image
    EffectName : TextBlockRef
    Details : TextBlockRef
}

def rogue_ui_widget(widget : UserWidgetRef) : ue_api_umg_input::UserWidget {
    return ue_ref(type<ue_api_umg_input::UserWidget>, widget.handle)
}

def rogue_ui_fraction(value, maximum : float) : float {
    return maximum > 0.0f ? clamp(value / maximum, 0.0f, 1.0f) : 0.0f
}

def rogue_ui_visibility(widget : UserWidgetRef; visible : bool) : void {
    let target = ue_ref(type<Widget>, widget.handle)
    ue_widget_SetVisibility(target, visible ? E_ESlateVisibility_d128c9c0.v_HitTestInvisible : E_ESlateVisibility_d128c9c0.v_Collapsed)
}
