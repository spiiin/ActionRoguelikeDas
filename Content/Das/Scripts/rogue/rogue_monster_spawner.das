options gen2
module rogue_monster_spawner public
require rogue_ai_character public
require ue_api_math public

// A spawn primitive for the later director: class/actions/loot come from MonsterData.
// Budget, waves and spawn positions deliberately belong to the director, not this component.
[ue_class(module_id="rogue", Blueprintable)]
class RogueMonsterSpawner : ActorComponent {
    state=ue_properties(BlueprintReadWrite) {
        var SpawnedMonsters:array<RogueAICharacterRef>
        var SpawnRequests:int=0
        var SpawnFailures:int=0
    }

    def BeginPlay():void { self.SetComponentTickEnabled(false) }

    [ue_function(BlueprintCallable)]
    def SpawnMonster(data:RogueMonsterDataRef; location:UEVector; rotation:UERotator):RogueAICharacterRef {
        self.SpawnRequests += 1
        let base=ue_class_loaded(type<ObjectRef>,"/Game/DasRogue/AI/BP_RogueAICharacter.BP_RogueAICharacter_C")
        if (!ue_is_valid(data) || !ue_class_valid(data.MonsterClass) ||
            !ue_static(KismetMathLibrary.ClassIsChildOf,data.MonsterClass,base)) {
            self.SpawnFailures += 1
            return default<RogueAICharacterRef>
        }
        let monster=ue_actor_spawn(type<RogueAICharacterRef>,data.MonsterClass,
            ue_transform(location,rotation,UE_VECTOR_ONE),ue_self_actor(),"AdjustIfPossibleButDontSpawnIfColliding")
        if (!ue_is_valid(monster)) {
            self.SpawnFailures += 1
            return monster
        }
        if (!monster.ConfigureMonsterData(data)) {
            ue_actor_destroy_handle(monster.handle)
            self.SpawnFailures += 1
            return default<RogueAICharacterRef>
        }
        var live:array<RogueAICharacterRef>
        for (existing in self.SpawnedMonsters) { if (ue_is_valid(existing)) { push(live,existing) } }
        push(live,monster)
        self.SpawnedMonsters := live
        return monster
    }

    [ue_function(BlueprintCallable)]
    def ClearMonsters():void {
        for (monster in self.SpawnedMonsters) {
            if (!ue_is_valid(monster)) { continue }
            // APawn destruction detaches and destroys its non-player controller natively.
            ue_actor_destroy_handle(monster.handle)
        }
        clear(self.SpawnedMonsters)
    }

    def EndPlay(reason:int):void { self.ClearMonsters() }
}

typedef RogueMonsterSpawnerRef=UEObjectRef("rogue.RogueMonsterSpawner")
