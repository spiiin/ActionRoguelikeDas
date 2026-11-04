options gen2
module rogue_director_slot public
require rogue_director_host public
require rogue_director_config public
require ue_data_tables public
require ue_random public
require math public

typedef RogueDirectorHostRef = UEInterfaceRef("rogue.RogueDirectorHost")

// One owned runtime object per original FRogueDirectorData entry.
[ue_class(module_id="rogue", type_folder="/Game/DasRogue/Types", Blueprintable)]
class RogueDirectorSlot : ScriptObject {
    state = ue_properties(BlueprintReadWrite) {
        var Config : RogueDirectorConfigRef
        var Host : RogueDirectorHostRef
        var Index : int = 0
        var Seed : int = 0
        var InitialSeed : int = 0
        var Active : bool = false
        var Credits : float = 0.0f
        var NextTickTime : double = 0.0lf
        var Options : array<RogueMonsterSpawnData>
        var RowNames : array<string>
        var Pending : bool = false
        var Query : EnvQueryRunRef
        var PendingProfile : SoftObject
        var PendingCost : float = 0.0f
        var SpawnLocation : UEVector
        var Attempts : int = 0
        var Selections : int = 0
        var Spawned : int = 0
        var Failures : int = 0
        var Unaffordable : int = 0
        var CapBlocks : int = 0
        var LastSelectedRow : string
    }

    [ue_function(BlueprintCallable)]
    def Configure(config : RogueDirectorConfigRef; host : ObjectRef; index, seed : int) : void {
        self.Config = config
        self.Host = ue_ref(type<RogueDirectorHostRef>, host.handle)
        self.Index = index
        self.Seed = seed
        self.InitialSeed = seed
        self.Credits = max(0.0f, config.StartingCredits)
        var rows : array<RogueMonsterSpawnData>
        var names : array<string>
        if (ue_is_valid(config.MonsterSpawnTable)) {
            var keys <- ue_data_table_names(config.MonsterSpawnTable.handle)
            // Stable row-name ordering makes a seed independent of TMap iteration order.
            sort(keys)
            for (name in keys) {
                let row = ue_data_table_row(type<RogueMonsterSpawnData>, config.MonsterSpawnTable.handle, name, "/Game/DasRogue/Types")
                if (!ue_soft_is_null(row.MonsterData) && is_finite(row.SpawnCost) && row.SpawnCost >= 0.0f &&
                    is_finite(row.SpawnWeight) && row.SpawnWeight > 0.0f) {
                    push(rows, row)
                    push(names, name)
                }
            }
        }
        self.Options := rows
        self.RowNames := names
    }

    [ue_function(BlueprintCallable)]
    def SetActive(active : bool) : void {
        self.Active = active
        if (!active) { self.CancelPending() }
    }

    [ue_function(BlueprintCallable)]
    def Step(time : double; delta : float) : void {
        if (!self.Active || !ue_is_valid(self.Config)) { return }
        let rate = rogue_director_income(self.Config.CreditGainCurve, float(time), self.Config.CreditsPerSecond)
        if (is_finite(rate) && rate >= 0.0f) { self.Credits += rate * delta }
        if (self.Pending || time < self.NextTickTime) { return }
        self.Attempts += 1
        if (!self.Host.ReserveSlot(self.Index)) {
            self.CapBlocks += 1
            self.NextTickTime = time + double(max(0.1f, self.Config.TimeBetweenWaves))
            return
        }
        var total = 0.0f
        for (row in self.Options) { total += row.SpawnWeight }
        if (!is_finite(total) || total <= 0.0f || !ue_is_valid(self.Config.SpawnLocationQuery)) {
            self.Host.ReleaseSlot(self.Index)
            self.FailedAttempt()
            return
        }
        var stream = self.Seed
        let weight = ue_random_float(stream, 0.0f, total)
        self.Seed = stream
        var accumulated = 0.0f
        var selected = length(self.Options) - 1
        for (i in range(length(self.Options))) {
            accumulated += self.Options[i].SpawnWeight
            if (weight <= accumulated) { selected = i; break }
        }
        let row = self.Options[selected]
        self.Selections += 1
        self.LastSelectedRow = self.RowNames[selected]
        if (self.Credits < row.SpawnCost) {
            self.Host.ReleaseSlot(self.Index)
            self.Unaffordable += 1
            self.NextTickTime = time + double(max(0.1f, self.Config.TimeBetweenWaves))
            return
        }
        self.Credits -= row.SpawnCost
        self.PendingCost = row.SpawnCost
        self.PendingProfile = row.MonsterData
        self.Pending = true
        self.Query = ue_environment_query(self.Config.SpawnLocationQuery, ue_ref(type<ActorRef>, self.Host.handle))
        if (!ue_is_valid(self.Query)) { self.FailPending(); return }
        self.Query.OnQueryFinishedEvent += self.OnQueryFinished
        self.NextTickTime = time + double(max(0.0f, self.Config.TickInterval))
    }

    def OnQueryFinished(query : EnvQueryRunRef; status : EnvQueryStatus) : void {
        if (!self.Pending || !ue_is_valid(self.Query) || !ue_same_object(query, self.Query)) { return }
        self.Query.OnQueryFinishedEvent -= self.OnQueryFinished
        self.Query = default<EnvQueryRunRef>
        if (!self.Active || status != EnvQueryStatus.Success) { self.FailPending(); return }
        let points <- ue_environment_query_locations(query)
        if (length(points) == 0) { self.FailPending(); return }
        self.SpawnLocation = points[0]
        ue_soft_load_async("MonsterProfile", self.PendingProfile, "OnProfileLoaded")
    }

    [ue_function(BlueprintCallable)]
    def OnProfileLoaded(value : ObjectRef) : void {
        if (!self.Pending || !self.Active) { return }
        if (!ue_is_valid(value) || !ue_object_is_a(value.handle, "/Game/DasRogue/Types/BP_RogueMonsterData.BP_RogueMonsterData_C")) {
            self.FailPending()
            return
        }
        if (self.Host.SpawnReserved(self.Index, value, self.SpawnLocation)) {
            self.Pending = false
            self.PendingCost = 0.0f
            self.Spawned += 1
        } else { self.FailPending() }
    }

    def FailedAttempt() : void {
        self.Failures += 1
        self.NextTickTime = ue_world_seconds() + double(max(0.1f, self.Config.TimeBetweenWaves))
    }

    def FailPending() : void {
        if (self.Pending) {
            self.Host.ReleaseSlot(self.Index)
            self.Credits += self.PendingCost
            self.PendingCost = 0.0f
            self.Pending = false
        }
        self.FailedAttempt()
    }

    // The host clears the reservation ledger before stopping its slots.
    def CancelPending() : void {
        if (ue_is_valid(self.Query)) {
            self.Query.OnQueryFinishedEvent -= self.OnQueryFinished
            ue_environment_query_abort(self.Query)
            self.Query = default<EnvQueryRunRef>
        }
        ue_asset_cancel("MonsterProfile")
        if (self.Pending) {
            self.Credits += self.PendingCost
            self.PendingCost = 0.0f
            self.Pending = false
        }
    }
}

typedef RogueDirectorSlotRef = UEObjectRef("rogue.RogueDirectorSlot")
