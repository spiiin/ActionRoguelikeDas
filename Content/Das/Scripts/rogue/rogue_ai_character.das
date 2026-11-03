options gen2
module rogue_ai_character public
require rogue_attribute_component public
require rogue_action_system_component public
require ue_ai public
require ue_vector_math public

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
    ActionSystem : RogueActionSystemComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category="AI") {
        var MoveSpeed : float = 250.0f
        var DeathDelay : float = 2.0f
        var AttackClass : ObjectClass
    }

    state = ue_properties(BlueprintReadWrite) {
        var Target : ActorRef
        var Dead : bool = false
        var Stunned : bool = false
        var Hits : int = 0
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
        self.CharacterMovement.MaxWalkSpeed = self.MoveSpeed
        self.CharacterMovement.bOrientRotationToMovement = false
        self.CharacterMovement.bUseControllerDesiredRotation = true
        self.CharacterMovement.RotationRate = ue_rotator(0.0lf, 360.0lf, 0.0lf)
        self.Visual.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        self.CapsuleComponent.SetCollisionResponseToChannel(ECollisionChannel.ECC_GameTraceChannel2, ECollisionResponse.ECR_Block)
        self.ActionSystem.SetBaseMoveSpeed(self.MoveSpeed)
        if (ue_class_valid(self.AttackClass)) { self.ActionSystem.GrantAction(self.AttackClass) }
        self.RefreshLabel()
        ue_self_actor().SetActorTickEnabled(false)
    }

    def BindEvents() : void {
        self.Attributes.OnHealthChanged += self.OnHealthChanged
        self.ActionSystem.GameplayTagUpdated += self.OnStatusChanged
    }

    def OnHealthChanged(instigator:ActorRef; health:float; delta:float) : void {
        if (delta < 0.0f) { self.Hits += 1 }
        if (health <= 0.0f && !self.Dead) {
            self.Dead = true
            self.Target = default<ActorRef>
            self.ActionSystem.Shutdown()
            self.CharacterMovement.StopMovementImmediately()
            self.CharacterMovement.DisableMovement()
            self.CapsuleComponent.SetCollisionEnabled(ECollisionEnabled.NoCollision)
            let controller = ue_character_self().GetController()
            // Native timer teardown runs outside this damage callback's script context.
            if (ue_is_valid(controller)) { ue_ref(type<ActorRef>,controller.handle).SetLifeSpan(0.01f) }
            self.SetLifeSpan(self.DeathDelay)
        }
        self.RefreshLabel()
    }

    def OnStatusChanged(tag:GameplayTag; count:int) : void {
        if (self.Dead) { return }
        self.Stunned = ue_tags_has(self.ActionSystem.GetActiveTags(),ue_tag("StatusEffect.Stunned"))
        self.CharacterMovement.MaxWalkSpeed = self.Stunned ? 0.0f : self.MoveSpeed
        if (self.Stunned) { self.CharacterMovement.StopMovementImmediately() }
        self.RefreshLabel()
    }

    def RefreshLabel() : void {
        let state = self.Dead ? "DEAD" : self.Stunned ? "STUNNED" : "AI enemy"
        self.Label.K2_SetText(ue_text_invariant("{state} | HP: {int(self.Attributes.Health)}"))
    }

    def EndPlay(reason:int) : void { self.ActionSystem.Shutdown() }
}

// Shared alias alongside the declaration; no additional refs file is required.
typedef RogueAICharacterRef = UEObjectRef("rogue.RogueAICharacter")
