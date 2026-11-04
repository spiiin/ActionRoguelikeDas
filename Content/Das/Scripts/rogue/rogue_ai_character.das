options gen2
module rogue_ai_character public
require rogue_attribute_component public
require rogue_hit_flash_component public
require rogue_action_system_component public
require rogue_presentation public
require rogue_action_drop_loot public
require rogue_monster_data public
require ue_ai public
require ue_perception public
require ue_vector_math public
require math public

// First combat slice of Tom Looman's RogueAICharacter (992f860); gameplay is daScript.
[ue_class(module_id="rogue", Blueprintable)]
class RogueAICharacter : Character {
    @ue_component
    Visual : StaticMeshComponentRef

    @ue_component
    Label : TextRenderComponentRef

    @ue_component
    Attributes : RogueAttributeComponentRef

    @ue_component
    HitFlash : RogueHitFlashComponentRef

    @ue_component
    ActionSystem : RogueActionSystemComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="AI") {
        var MoveSpeed : float = 450.0f
        var DeathDelay : float = 10.0f
        var AttackClass : ObjectClass
        var DropLootActionClass : ObjectClass
        var MonsterData : RogueMonsterDataRef
        var UseExternalPresentation : bool = true
        var PresentationProfilePath : string = "/Game/DasRogueExternal/DA_MinionPresentation.DA_MinionPresentation"
    }

    state = ue_properties(BlueprintReadWrite) {
        var Target : ActorRef
        var Dead : bool = false
        var Stunned : bool = false
        var Hits : int = 0
        var Presentation : RoguePresentationProfileRef
        var UsingExternalPresentation : bool = false
        var NextHitReactionAt : double = -1.0lf
        var HitReactions : int = 0
        var StunAnimations : int = 0
        var DeathAnimations : int = 0
        var LootDrops : int = 0
        var LastLootCoins : int = 0
    }

    defaults = ue_defaults() {
        self.Visual.StaticMesh = ue_asset_default("/Engine/BasicShapes/Cone.Cone")
        self.Visual.RelativeScale3D = ue_vector(0.65lf, 0.65lf, 1.7lf)
        self.Visual.RelativeRotation = UE_ROTATOR_ZERO
        self.Label.RelativeLocation = ue_vector(0.0lf, 0.0lf, 115.0lf)
        self.Label.WorldSize = 22.0f
        self.bUseControllerRotationYaw = false
    }

    def BeginPlay() : void {
        self.ActionSystem.ConfigureAttributeSet(ue_class_loaded(type<ObjectClass>, "/Game/DasRogue/Attributes/BP_RogueMonsterAttributeSet.BP_RogueMonsterAttributeSet_C"))
        if (self.UseExternalPresentation) { self.Presentation = rogue_load_presentation(self.PresentationProfilePath) ?? default<RoguePresentationProfileRef> }
        if (ue_is_valid(self.Presentation) && ue_is_valid(self.Presentation.CharacterMesh)) {
            rogue_apply_mesh(self.Mesh, self.Presentation)
            self.Mesh.SetCollisionProfileName(ue_name_value("NoCollision"), true)
            self.Visual.SetHiddenInGame(true, false)
            self.UsingExternalPresentation = true
        }
        self.CharacterMovement.MaxWalkSpeed = self.MoveSpeed
        self.CharacterMovement.bOrientRotationToMovement = false
        self.CharacterMovement.bUseControllerDesiredRotation = true
        self.CharacterMovement.RotationRate = ue_rotator(0.0lf, 360.0lf, 0.0lf)
        self.Visual.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        self.CapsuleComponent.SetCollisionResponseToChannel(ECollisionChannel.ECC_GameTraceChannel2, ECollisionResponse.ECR_Block)
        self.ActionSystem.SetBaseMoveSpeed(self.MoveSpeed)
        if (ue_class_valid(self.AttackClass)) {
            let action = self.ActionSystem.GrantAction(self.AttackClass)
            if (ue_is_valid(action) && self.UsingExternalPresentation) {
                rogue_apply_attack(ue_ref(type<RogueProjectileAttackRef>, action.handle), self.Presentation)
            }
        }
        self.RefreshLabel()
        ue_self_actor().SetActorTickEnabled(false)
    }

    def BindEvents() : void {
        self.Attributes.OnHealthChanged += self.OnHealthChanged
        self.ActionSystem.GameplayTagUpdated += self.OnStatusChanged
    }

    def OnHealthChanged(instigator:ActorRef; health:float; delta:float) : void {
        if (self.Dead) { return }
        if (delta < 0.0f) { self.Hits += 1 }
        if (health <= 0.0f) { self.HandleDeath() }
        self.RefreshLabel()
    }

    def HandleDeath() : void {
        self.Dead = true
        self.Target = default<ActorRef>
        self.DropLoot()
        self.ActionSystem.Shutdown()
        self.CharacterMovement.StopMovementImmediately()
        self.CharacterMovement.DisableMovement()
        self.CapsuleComponent.SetCollisionEnabled(ECollisionEnabled.NoCollision)
        let controller = ue_character_self().GetController()
        // This port's thinker lives on the controller rather than a BehaviorTree brain.
        if (ue_is_valid(controller)) {
            controller.StopMovement()
            let actor = ue_ref(type<ActorRef>,controller.handle)
            actor.SetActorTickEnabled(false)
            actor.SetLifeSpan(self.DeathDelay + 0.1f)
        }
        // Original death uses physics, with animations paused rather than a death montage.
        self.Mesh.bPauseAnims = true
        self.Mesh.SetCollisionProfileName(ue_name_value("Ragdoll"), true)
        self.Mesh.SetAllBodiesSimulatePhysics(true)
        self.Label.SetHiddenInGame(true, false)
        self.SetLifeSpan(self.DeathDelay)
    }

    def DropLoot() : void {
        if (!ue_class_valid(self.DropLootActionClass)) { return }
        let action = self.ActionSystem.GrantAction(self.DropLootActionClass)
        if (!ue_is_valid(action)) { return }
        let loot = ue_ref(type<RogueActionDropLootRef>, action.handle)
        loot.CreditsToDrop = ue_is_valid(self.MonsterData) ? max(self.MonsterData.LootCoins, 0) : 10
        if (self.ActionSystem.StartAction(ue_tag("Action.DropLoot")) && loot.HasDropped) {
            self.LootDrops += 1
            self.LastLootCoins = loot.DroppedCredits
        }
    }

    [ue_event(source=self, name=OnTakeAnyDamage)]
    def OnDamage(damaged:ActorRef; amount:float; kind:ObjectRef; instigator:ObjectRef; source:ActorRef) : void {
        if (amount <= 0.0f || !ue_is_valid(instigator)) { return }
        let controller = ue_ref(type<ControllerRef>, instigator.handle)
        let observer = ue_character_self().GetController()
        if (!ue_is_valid(observer) || ue_controller_is_friendly(observer, ue_ref(type<ActorRef>, controller.handle))) { return }
        let pawn = controller.K2_GetPawn()
        if (!ue_is_valid(pawn)) { return }
        let actor = ue_ref(type<ActorRef>, pawn.handle)
        ue_perception_report_damage(ue_self_actor(), actor, amount, actor.K2_GetActorLocation(), self.K2_GetActorLocation())
    }

    def OnStatusChanged(tag:GameplayTag; count:int) : void {
        if (self.Dead) { return }
        let wasStunned = self.Stunned
        self.Stunned = ue_tags_has(self.ActionSystem.GetActiveTags(),ue_tag("StatusEffect.Stunned"))
        // Attribute changes may refresh speed during stun; the movement mode remains disabled.
        if (self.Stunned != wasStunned) {
            if (self.Stunned) {
                self.CharacterMovement.DisableMovement()
                self.CharacterMovement.StopMovementImmediately()
            } else {
                self.CharacterMovement.SetMovementMode(EMovementMode.MOVE_Walking)
            }
        }
        self.UpdateStunAnimation(wasStunned)
        self.RefreshLabel()
    }

    def UpdateStunAnimation(wasStunned : bool) : void {
        if (self.Stunned == wasStunned || !self.UsingExternalPresentation) { return }
        if (!ue_is_valid(self.Presentation.StunMontage)) { return }
        if (!self.Stunned) {
            self.StopAnimMontage(self.Presentation.StunMontage)
            return
        }
        let duration = ue_character_play_montage(ue_character_self(), self.Presentation.StunMontage)
        if (duration > 0.0f) { self.StunAnimations += 1 }
    }

    def RefreshLabel() : void {
        let state = self.Dead ? "DEAD" : self.Stunned ? "STUNNED" : "AI enemy"
        self.Label.K2_SetText(ue_text_invariant("{state} | HP: {int(self.Attributes.Health)}"))
    }

    def EndPlay(reason:int) : void { self.ActionSystem.Shutdown() }
}

// Shared alias alongside the declaration; no additional refs file is required.
typedef RogueAICharacterRef = UEObjectRef("rogue.RogueAICharacter")
