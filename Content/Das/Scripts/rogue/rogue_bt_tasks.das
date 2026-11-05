options gen2
module rogue_bt_tasks public
require rogue_tags public
require rogue_ai_character public
require rogue_patrol_point public
require ue_behavior_tree public
require ue_api_world public
require ue_api_math public
require math public

[ue_class(module_id="rogue", Blueprintable)]
class RogueBTHealSelf : BTTask {
    @ue_property=(EditAnywhere, BlueprintReadWrite)
    HealAmount:float=100.0f

    [ue_function(BlueprintEvent)]
    def ReceiveExecuteAI(OwnerController:AIControllerRef; ControlledPawn:NativePawnRef):void {
        let system=ue_component_find(type<RogueActionSystemComponentRef>,ue_ref(type<ActorRef>,ControlledPawn.handle))
        if (ue_is_valid(system) && system.IsActionOwnerAlive()) {
            system.ApplyAttributeChange(rogue_tag_health(),self.HealAmount)
            ue_bt_finish(true)
        } else { ue_bt_finish(false) }
    }
}

[ue_class(module_id="rogue", Blueprintable)]
class RogueBTLowHealth : BTDecorator {
    @ue_property=(EditAnywhere, BlueprintReadWrite)
    LowHealthFraction:float=0.3f

    [ue_function(BlueprintEvent)]
    def PerformConditionCheckAI(OwnerController:AIControllerRef; ControlledPawn:NativePawnRef):bool {
        let attributes=ue_component_find(type<RogueAttributeComponentRef>,ue_ref(type<ActorRef>,ControlledPawn.handle))
        if (!ue_is_valid(attributes) || !attributes.IsAlive() || attributes.HealthMax<=0.0f) { return false }
        return attributes.Health/attributes.HealthMax < self.LowHealthFraction
    }
}

[ue_class(module_id="rogue", Blueprintable)]
class RogueBTCheckRange : BTService {
    @ue_property=(EditAnywhere, BlueprintReadWrite)
    MaxAttackRange:float=1000.0f

    [ue_function(BlueprintEvent)]
    def ReceiveTickAI(OwnerController:AIControllerRef; ControlledPawn:NativePawnRef; DeltaSeconds:float):void {
        let board=ue_ai_blackboard(OwnerController)
        let target=ue_blackboard_object(board,"TargetActor")
        let origin=ue_ref(type<ActorRef>,ControlledPawn.handle).K2_GetActorLocation()
        let within=(ue_is_valid(target) && length(target.K2_GetActorLocation()-origin)<double(self.MaxAttackRange)
            && ue_ai_line_of_sight(OwnerController,target))
        ue_blackboard_set_bool(board,"WithinRange",within)
        // Keep presentation and the existing DAS attack's aim in sync with the selected target.
        ue_ref(type<RogueAICharacterRef>,ControlledPawn.handle).Target=target
    }
}

[ue_class(module_id="rogue", Blueprintable)]
class RogueBTRangedAttack : BTTask {
    [ue_function(BlueprintEvent)]
    def ReceiveExecuteAI(OwnerController:AIControllerRef; ControlledPawn:NativePawnRef):void {
        let enemy=ue_ref(type<RogueAICharacterRef>,ControlledPawn.handle)
        let target=ue_blackboard_object(ue_ai_blackboard(OwnerController),"TargetActor")
        if (enemy.Dead || !ue_is_valid(target)) { ue_bt_finish(false); return }
        enemy.Target=target
        let action=enemy.ActionSystem.FindAction(rogue_tag_primary_attack())
        if (!ue_is_valid(action)) { ue_bt_finish(false); return }
        let attack=ue_ref(type<RogueProjectileAttackRef>,action.handle)
        let before=attack.ProjectilesFired
        attack.FireProjectile()
        ue_bt_finish(attack.ProjectilesFired>before)
    }
}

[ue_class(module_id="rogue", Blueprintable)]
class RogueBTFindPatrol : BTTask {
    @ue_property=(EditAnywhere, BlueprintReadWrite)
    PatrolPointClass:ActorClass

    [ue_function(BlueprintEvent)]
    def ReceiveExecuteAI(OwnerController:AIControllerRef; ControlledPawn:NativePawnRef):void {
        if (!ue_class_valid(self.PatrolPointClass)) { ue_bt_finish(false); return }
        let board=ue_ai_blackboard(OwnerController)
        var current=ue_ref(type<RoguePatrolPointRef>,ue_blackboard_object(board,"CurrentPatrolPoint").handle)
        if (!ue_is_valid(current)) {
            let origin=ue_ref(type<ActorRef>,ControlledPawn.handle).K2_GetActorLocation()
            let points <- ue_static(GameplayStatics.GetAllActorsOfClass,self.PatrolPointClass)
            var nearest=1.0e30lf
            for (point in points) {
                let distance=length_sq(point.K2_GetActorLocation()-origin)
                if (distance<nearest) { current=ue_ref(type<RoguePatrolPointRef>,point.handle); nearest=distance }
            }
        }
        if (!ue_is_valid(current)) { ue_bt_finish(false); return }
        var choices := current.NearbyPatrolPoints
        let previous=ue_blackboard_object(board,"PreviousPatrolPoint")
        var valid:array<ActorRef>
        for (point in choices) {
            if (ue_is_valid(point) && (length(choices)<=1 || !ue_same_object(point,previous))) { push(valid,point) }
        }
        if (length(valid)==0) { ue_bt_finish(false); return }
        let index=ue_static(KismetMathLibrary.RandomIntegerInRange,0,length(valid)-1)
        ue_blackboard_set_object(board,"PreviousPatrolPoint",ue_ref(type<ActorRef>,current.handle))
        ue_blackboard_set_object(board,"CurrentPatrolPoint",valid[index])
        ue_bt_finish(true)
    }
}

[ue_class(module_id="rogue", Blueprintable)]
class RogueEQSTarget : EQSContext {
    [ue_function(BlueprintEvent)]
    def const ProvideSingleActor(QuerierObject:ObjectRef; QuerierActor:ActorRef; @ue_out var ResultingActor:ActorRef&):void {
        ResultingActor=default<ActorRef>
        if (!ue_is_valid(QuerierActor) || !ue_object_is_a(QuerierActor.handle,"/Script/Engine.Pawn")) { return }
        let controller=ue_ref(type<NativePawnRef>,QuerierActor.handle).GetController()
        if (!ue_is_valid(controller)) { return }
        let board=ue_ai_blackboard(ue_ref(type<AIControllerRef>,controller.handle))
        if (ue_object_valid(board)) { ResultingActor=ue_blackboard_object(board,"TargetActor") }
    }
}
