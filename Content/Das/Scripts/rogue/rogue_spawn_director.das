options gen2
module rogue_spawn_director public
require rogue_director_slot public
require rogue_monster_spawner public
require ue_api_world public

// All slots share one reservation ledger, so concurrent queries cannot exceed the cap.
[ue_class(module_id="rogue", Blueprintable), ue_implements(interface="/Game/DasRogue/Types/RogueDirectorHost.RogueDirectorHost_C")]
class RogueSpawnDirector : Actor {
    @ue_component
    Spawner : RogueMonsterSpawnerRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="Director") {
        var AutoStart : bool = true
        var SlotClass : ObjectClass
        var BotLimit : int = 5
        var GlobalStartingSeed : int = 42
        var Configurations : array<RogueDirectorConfigRef>
        var MonsterBase : ActorClass
    }

    state = ue_properties(BlueprintReadWrite) {
        var Enabled : bool = false
        var Slots : array<RogueDirectorSlotRef>
        var Reservations : array<int>
        var NextUpdate : double = 0.0lf
        var LastUpdate : double = 0.0lf
        var TotalSpawned : int = 0
    }

    defaults = ue_defaults() {
        self.SlotClass = ue_class_default("/Game/DasRogue/Director/BP_RogueDirectorSlot.BP_RogueDirectorSlot_C")
        self.MonsterBase = ue_class_default("/Game/DasRogue/AI/BP_RogueAICharacter.BP_RogueAICharacter_C")
    }

    def BeginPlay() : void {
        self.Configure(self.Configurations, self.GlobalStartingSeed, self.BotLimit)
        self.SetEnabled(self.AutoStart)
    }

    [ue_function(BlueprintCallable)]
    def Configure(configs : array<RogueDirectorConfigRef>; seed, limit : int) : void {
        self.Shutdown()
        self.Configurations := configs
        self.GlobalStartingSeed = seed
        self.BotLimit = max(0, limit)
        if (!rogue_director_authority()) { return }
        var stream = seed
        var slots : array<RogueDirectorSlotRef>
        for (index in range(length(configs))) {
            if (!ue_is_valid(configs[index])) { continue }
            let slot = ue_object_new(type<RogueDirectorSlotRef>, self.SlotClass, ue_ref(type<ObjectRef>, ue_self_object()))
            push(slots, slot)
            slot.Configure(configs[index], ue_ref(type<ObjectRef>, ue_self_object()), index,
                ue_random_int(stream, 0, 2147483646))
        }
        self.Slots := slots
    }

    [ue_function(BlueprintCallable)]
    def SetEnabled(enabled : bool) : void {
        self.Enabled = enabled && rogue_director_authority()
        if (self.Enabled) {
            self.LastUpdate = ue_world_seconds()
            self.NextUpdate = self.LastUpdate
        }
        if (!self.Enabled) {
            var reservations : array<int>
            self.Reservations := reservations
        }
        for (slot in self.Slots) {
            if (ue_is_valid(slot)) { slot.SetActive(self.Enabled) }
        }
        self.SetActorTickEnabled(self.Enabled)
    }

    def Tick(delta : float) : void {
        if (!self.Enabled) { return }
        let time = ue_world_seconds()
        if (time < self.NextUpdate) { return }
        let elapsed = float(max(0.0lf, time - self.LastUpdate))
        self.LastUpdate = time
        self.NextUpdate = time + 0.1lf
        for (slot in self.Slots) { slot.Step(time, elapsed) }
    }

    [ue_function(BlueprintCallable)]
    def AliveCount() : int {
        var count = 0
        let actors <- ue_static(GameplayStatics.GetAllActorsOfClass, self.MonsterBase)
        for (actor in actors) {
            let enemy = ue_ref(type<RogueAICharacterRef>, actor.handle)
            if (ue_is_valid(enemy) && !enemy.Dead) { count += 1 }
        }
        return count
    }

    [ue_function(BlueprintCallable)]
    def ReserveSlot(index : int) : bool {
        if (!self.Enabled || !rogue_director_authority() || self.AliveCount() + length(self.Reservations) >= self.BotLimit) { return false }
        for (reserved in self.Reservations) { if (reserved == index) { return false } }
        push(self.Reservations, index)
        return true
    }

    [ue_function(BlueprintCallable)]
    def ReleaseSlot(index : int) : void {
        var reservations : array<int>
        for (reserved in self.Reservations) { if (reserved != index) { push(reservations, reserved) } }
        self.Reservations := reservations
    }

    [ue_function(BlueprintCallable)]
    def SpawnReserved(index : int; data : ObjectRef; location : UEVector) : bool {
        var reserved = false
        for (value in self.Reservations) { if (value == index) { reserved = true; break } }
        self.ReleaseSlot(index)
        if (!reserved || !self.Enabled || self.AliveCount() >= self.BotLimit) { return false }
        if (!ue_is_valid(self.Spawner.SpawnMonster(ue_ref(type<RogueMonsterDataRef>, data.handle), location, UE_ROTATOR_ZERO))) { return false }
        self.TotalSpawned += 1
        return true
    }

    [ue_function(BlueprintCallable)]
    def Shutdown() : void {
        self.SetEnabled(false)
        self.Spawner.ClearMonsters()
        var slots : array<RogueDirectorSlotRef>
        var reservations : array<int>
        self.Slots := slots
        self.Reservations := reservations
    }

    def EndPlay(reason : int) : void {
        // Unreal has already stopped native ticking; only release owned work here.
        self.Enabled = false
        var reservations : array<int>
        self.Reservations := reservations
        for (slot in self.Slots) {
            if (ue_is_valid(slot)) { slot.SetActive(false) }
        }
        if (ue_is_valid(self.Spawner)) { self.Spawner.ClearMonsters() }
        var slots : array<RogueDirectorSlotRef>
        self.Slots := slots
    }
}

typedef RogueSpawnDirectorRef = UEObjectRef("rogue.RogueSpawnDirector")
