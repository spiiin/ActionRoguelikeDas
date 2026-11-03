options gen2
module rogue_coin_pickup_subsystem public
require rogue_action_system_component public
require ue_instanced_mesh public
require ue_vector_math public
require ue_api_world public
require ue_subsystems public
require math public

// Per-owner VM data: no reflected-array copy per coin or Actor per instance.
var coin_locations : array<UEVector>
var coin_amounts : array<int>
var coin_mesh_ids : array<int>

typedef CoinMaterialRef = UENativeObjectRef("/Script/Engine.MaterialInterface")

// Batched world pickup model of URogueCoinPickupSubsystem, course commit 992f860.
[ue_class(module_id="rogue", Blueprintable)]
class RogueCoinPickupSubsystem : WorldSubsystem {
    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Coins") {
        var PickupRadius : float = 200.0f
        var CoinMesh : StaticMeshRef
        var CoinMaterial : CoinMaterialRef
        var CoinSound : SoundBaseRef
        var PickupTrigger : string = "OnPickup"
        var MeshScale : UEVector = ue_vector(0.3lf, 0.3lf, 0.06lf)
        var VisualOffset : UEVector = ue_vector(0.0lf, 0.0lf, 50.0lf)
        var AutoCollect : bool = true
    }

    state = ue_properties(BlueprintReadWrite) {
        // Outer alone does not retain world components: these are strong UPROPERTYs.
        var WorldISM : InstancedStaticMeshComponentRef
        var WorldAudio : WorldAudioComponentRef
        var Accepting : bool = false
        var CoinCount : int = 0
        var RemainingValue : int64 = 0l
        var CollectedValue : int64 = 0l
        var GrantCalls : int = 0
        var BatchesAdded : int = 0
    }

    defaults = ue_defaults() {
        self.CoinMesh = ue_asset_default("/Engine/BasicShapes/Cylinder.Cylinder")
        self.CoinMaterial = ue_asset_default("/Game/DasRogue/Materials/M_TargetHealth.M_TargetHealth")
    }

    def Initialize() : void {
        clear(coin_locations)
        clear(coin_amounts)
        clear(coin_mesh_ids)
        self.Accepting = true
    }

    [ue_function(BlueprintCallable)]
    def EnsureRenderer() : bool {
        if (!self.Accepting) { return false }
        if (ue_is_valid(self.WorldISM)) { return true }
        self.WorldISM = ue_world_ism_create("CoinInstances")
        if (!ue_is_valid(self.WorldISM)) { return false }
        self.WorldISM.SetCollisionEnabled(ECollisionEnabled.NoCollision)
        self.WorldISM.SetAffectDistanceFieldLighting(false)
        self.WorldISM.SetStaticMesh(self.CoinMesh)
        if (ue_is_valid(self.CoinMaterial)) {
            self.WorldISM.SetMaterial(0, self.CoinMaterial)
            self.WorldISM.SetVectorParameterValueOnMaterials(ue_name_value("Color"), ue_vector(1.0lf, 0.65lf, 0.03lf))
        }
        if (!ue_world_component_register(self.WorldISM)) {
            ue_world_component_destroy(self.WorldISM)
            self.WorldISM = default<InstancedStaticMeshComponentRef>
            return false
        }
        if (!empty(coin_locations)) {
            var transforms : array<UETransform>
            let offset = self.VisualOffset
            let scale = self.MeshScale
            for (location in coin_locations) { push(transforms, ue_transform(location+offset, UE_ROTATOR_ZERO, scale)) }
            coin_mesh_ids <- ue_ism_add_instances(self.WorldISM, transforms)
            verify(length(coin_mesh_ids) == length(coin_locations), "Cannot rebuild coin instances")
        }
        return true
    }

    [ue_function(BlueprintCallable)]
    def AddCoinPickups(locations : array<UEVector>; amounts : array<int>) : bool {
        if (!self.Accepting || length(locations) != length(amounts)) { return false }
        for (location, amount in locations, amounts) {
            if (amount <= 0 || !is_finite(location.x) || !is_finite(location.y) || !is_finite(location.z)) { return false }
        }
        if (empty(locations)) { return true }
        if (!self.EnsureRenderer()) { return false }
        var transforms : array<UETransform>
        let offset = self.VisualOffset
        let scale = self.MeshScale
        for (location in locations) { push(transforms, ue_transform(location+offset, UE_ROTATOR_ZERO, scale)) }
        let ids <- ue_ism_add_instances(self.WorldISM, transforms)
        if (length(ids) != length(locations)) { return false }
        for (location, amount, id in locations, amounts, ids) {
            push(coin_locations, location)
            push(coin_amounts, amount)
            push(coin_mesh_ids, id)
            self.RemainingValue += int64(amount)
        }
        self.CoinCount = length(coin_locations)
        self.BatchesAdded += 1
        return true
    }

    // Match the original parallel-array RemoveAtSwap, without moving stable mesh IDs.
    def RemoveAtSwap(index : int) : void {
        let last = length(coin_locations)-1
        if (index != last) {
            coin_locations[index] = coin_locations[last]
            coin_amounts[index] = coin_amounts[last]
            coin_mesh_ids[index] = coin_mesh_ids[last]
        }
        resize(coin_locations, last)
        resize(coin_amounts, last)
        resize(coin_mesh_ids, last)
    }

    [ue_function(BlueprintCallable)]
    def RemoveCoinPickup(index : int) : bool {
        if (index < 0 || index >= length(coin_locations) || !self.EnsureRenderer()) { return false }
        var ids : array<int>
        push(ids, coin_mesh_ids[index])
        if (!ue_ism_remove_instances(self.WorldISM, ids)) { return false }
        self.RemainingValue -= int64(coin_amounts[index])
        self.RemoveAtSwap(index)
        self.CoinCount = length(coin_locations)
        return true
    }

    def Tick(delta : float) : void {
        if (!self.EnsureRenderer() || !self.AutoCollect || empty(coin_locations) || !(self.PickupRadius > 0.0f)) { return }
        let player = ue_static(GameplayStatics.GetPlayerController, 0)
        if (!ue_is_valid(player)) { return }
        let pawn = ue_ref(type<PlayerControllerRef>, player.handle).K2_GetPawn()
        if (!ue_is_valid(pawn)) { return }
        let target = ue_ref(type<ActorRef>, pawn.handle)
        let attributes = ue_component_find(type<RogueAttributeComponentRef>, target)
        let actions = ue_component_find(type<RogueActionSystemComponentRef>, target)
        if (!ue_is_valid(attributes) || !attributes.IsAlive() || !ue_is_valid(actions) || !actions.IsActionOwnerAlive()) { return }
        let position = target.K2_GetActorLocation()
        let radius = double(self.PickupRadius)
        var indices : array<int>
        var ids : array<int>
        var total : int64 = 0l
        for (index in range(length(coin_locations))) {
            if (length_sq(position-coin_locations[index]) < radius*radius) {
                push(indices, index)
                push(ids, coin_mesh_ids[index])
                total += int64(coin_amounts[index])
            }
        }
        if (empty(indices) || !actions.CanReceiveCoins(total) || !ue_ism_remove_instances(self.WorldISM, ids)) { return }
        var remaining = length(indices)
        while (remaining > 0) {
            remaining -= 1
            self.RemoveAtSwap(indices[remaining])
        }
        self.CoinCount = length(coin_locations)
        self.RemainingValue -= total
        self.CollectedValue += total
        self.GrantCalls += 1
        verify(actions.GrantCoins(total), "Validated coin grant failed")
        self.PlayPickupSound()
    }

    def PlayPickupSound() : void {
        if (!ue_is_valid(self.CoinSound)) { return }
        if (!ue_is_valid(self.WorldAudio)) {
            self.WorldAudio = ue_world_audio_create("CoinAudio")
            if (!ue_is_valid(self.WorldAudio)) { return }
            self.WorldAudio.SetAutoActivate(false)
            self.WorldAudio.bAllowSpatialization = false
            self.WorldAudio.SetSound(self.CoinSound)
            if (!ue_world_component_register(self.WorldAudio)) { return }
        }
        if (!self.WorldAudio.IsPlaying()) { self.WorldAudio.Play(0.0f) }
        ue_audio_trigger(self.WorldAudio, self.PickupTrigger)
    }

    [ue_function(BlueprintPure)]
    def LocationAt(index : int) : UEVector {
        return index >= 0 && index < length(coin_locations) ? coin_locations[index] : UE_VECTOR_ZERO
    }

    [ue_function(BlueprintPure)]
    def AmountAt(index : int) : int {
        return index >= 0 && index < length(coin_amounts) ? coin_amounts[index] : 0
    }

    [ue_function(BlueprintPure)]
    def MeshIdAt(index : int) : int {
        return index >= 0 && index < length(coin_mesh_ids) ? coin_mesh_ids[index] : -1
    }

    def Deinitialize() : void {
        self.Accepting = false
        if (ue_is_valid(self.WorldISM)) { ue_world_component_destroy(self.WorldISM) }
        if (ue_is_valid(self.WorldAudio)) { ue_world_component_destroy(self.WorldAudio) }
        self.WorldISM = default<InstancedStaticMeshComponentRef>
        self.WorldAudio = default<WorldAudioComponentRef>
        clear(coin_locations)
        clear(coin_amounts)
        clear(coin_mesh_ids)
        self.CoinCount = 0
        self.RemainingValue = 0l
    }
}

typedef RogueCoinPickupSubsystemRef = UEObjectRef("rogue.RogueCoinPickupSubsystem")
