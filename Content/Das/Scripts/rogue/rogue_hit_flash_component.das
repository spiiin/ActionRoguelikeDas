options gen2
module rogue_hit_flash_component public
require ue_animation public
require ue_native_gameplay public
require ue_effects public

// One owner-local timer: repeated native damage restarts the original one-second window.
typedef RogueHitMaterialRef = UENativeObjectRef("/Script/Engine.MaterialInterface")

[ue_class(module_id="rogue", Blueprintable)]
class RogueHitFlashComponent : ActorComponent {
    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Hit Flash") {
        var OverlayMaterial : RogueHitMaterialRef
    }

    state = ue_properties(BlueprintReadWrite) {
        var Mesh : SkeletalMeshComponentRef
        var Flashes : int = 0
        var LastHitTime : float = -1.0f
        var Visible : bool = false
    }

    defaults = ue_defaults() {
        self.OverlayMaterial = ue_asset_default("/Game/DasRogue/Materials/M_HitFlash.M_HitFlash")
    }

    def BeginPlay() : void {
        let owner = ue_ref(type<CharacterRef>, ue_component_owner(ue_self_object()))
        self.Mesh = owner.Mesh
        if (ue_is_valid(self.OverlayMaterial)) { self.Mesh.SetOverlayMaterial(self.OverlayMaterial, false, 0) }
        self.Mesh.SetOverlayMaterialMaxDrawDistance(1.0f)
        self.SetComponentTickEnabled(false)
    }

    [ue_event(source=owner, source_type=ActorRef, name=OnTakeAnyDamage)]
    def OnDamage(damaged:ActorRef; amount:float; kind:ObjectRef; controller:ObjectRef; source:ActorRef) : void {
        if (amount <= 0.0f || !ue_is_valid(self.Mesh)) { return }
        self.LastHitTime = float(ue_world_seconds())
        self.Mesh.SetCustomPrimitiveDataFloat(0, self.LastHitTime)
        self.Mesh.SetOverlayMaterialMaxDrawDistance(0.0f)
        self.Visible = true
        self.Flashes += 1
        ue_timer_start("HitOverlay", 1.0f, self.HideOverlay, false)
    }

    [ue_function]
    def HideOverlay() : void {
        self.Visible = false
        self.Mesh.SetOverlayMaterialMaxDrawDistance(1.0f)
    }
}

typedef RogueHitFlashComponentRef = UEObjectRef("rogue.RogueHitFlashComponent")
