options gen2
module rogue_monster_probe public
require rogue_monster_spawner public

[ue_class(module_id="roguetest", Blueprintable)]
class RogueMonsterProbe : Actor {
    @ue_component
    Spawner:RogueMonsterSpawnerRef

    def BeginPlay():void { self.SetActorTickEnabled(false) }
}
