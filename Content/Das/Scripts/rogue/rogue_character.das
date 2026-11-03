options gen2
module rogue_character public
require rogue_attribute_component public
require rogue_action_system_component public
require rogue_presentation public
require math
require ue_vector_math public

// Movement, camera and initial health/death slice of RoguePlayerCharacter, commit 992f860.
// Publication permission and redistribution license are pending.
[ue_class(module_id="rogue", Blueprintable)]
class RogueCharacter : Character {
    @ue_component
    SpringArmComponent : SpringArmComponentRef

    @ue_component
    @Attach = "SpringArmComponent"
    @AttachSocket = "SpringEndpoint"
    CameraComponent : CameraComponentRef

    @ue_component
    Visual : StaticMeshComponentRef

    @ue_component
    Attributes : RogueAttributeComponentRef

    @ue_component
    HealthLabel : TextRenderComponentRef

    @ue_component
    ActionSystem : RogueActionSystemComponentRef

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Input") {
        var UseExternalPresentation : bool = true
        var PresentationProfilePath : string = "/Game/DasRogueExternal/DA_Presentation.DA_Presentation"
        var WalkSpeed : float = 450.0f
        var JumpVelocity : float = 500.0f
        var AirControl : float = 0.2f
        var Controls : InputMappingContextRef
        var Input_Move : InputActionRef
        var Input_Look : InputActionRef
        var Input_Jump : InputActionRef
        var Input_Sprint : InputActionRef
        var SprintActionClass : ObjectClass
        var AttackActionClass : ObjectClass
        var Input_TestDamage : InputActionRef
        var TestDamage : float = 25.0f
    }

    state = ue_properties(BlueprintReadWrite) {
        var Presentation : RoguePresentationProfileRef
        var UsingExternalPresentation : bool = false
        var Dead : bool = false
        var DeathCount : int = 0
        var ControlsBound : bool = false
        var MoveEvents : int = 0
        var LookEvents : int = 0
        var JumpPresses : int = 0
        var JumpReleases : int = 0
    }

    defaults = ue_defaults() {
        self.Controls = ue_asset_default("/Game/DasRogue/Input/IMC_Character.IMC_Character")
        self.Input_Move = ue_asset_default("/Game/DasRogue/Input/IA_Move.IA_Move")
        self.Input_Look = ue_asset_default("/Game/DasRogue/Input/IA_Look.IA_Look")
        self.Input_Jump = ue_asset_default("/Game/DasRogue/Input/IA_Jump.IA_Jump")
        self.Input_Sprint = ue_asset_default("/Game/DasRogue/Input/IA_Sprint.IA_Sprint")
        self.SprintActionClass = ue_class_default("/Game/DasRogue/Actions/BP_RogueActionSprint.BP_RogueActionSprint_C")
        self.AttackActionClass = ue_class_default("/Game/DasRogue/Actions/BP_RogueActionProjectileAttack.BP_RogueActionProjectileAttack_C")
        self.Input_TestDamage = ue_asset_default("/Game/DasRogue/Input/IA_TestDamage.IA_TestDamage")
        self.HealthLabel.RelativeLocation = ue_vector(0.0lf, 0.0lf, 120.0lf)
        self.HealthLabel.WorldSize = 20.0f
        self.bUseControllerRotationYaw = false
        self.bUseControllerRotationPitch = false
        self.bUseControllerRotationRoll = false
        self.SpringArmComponent.TargetArmLength = 350.0f
        self.SpringArmComponent.bUsePawnControlRotation = true
        self.SpringArmComponent.RelativeLocation = ue_vector(0.0lf, 0.0lf, 55.0lf)
        self.CameraComponent.bUsePawnControlRotation = false
        self.Visual.StaticMesh = ue_asset_default("/Engine/BasicShapes/Cone.Cone")
        self.Visual.RelativeScale3D = ue_vector(0.65lf, 0.65lf, 1.7lf)
        self.Visual.RelativeRotation = UE_ROTATOR_ZERO
    }

    def BeginPlay() : void {
        if (self.UseExternalPresentation) { self.Presentation = rogue_load_presentation(self.PresentationProfilePath) }
        if (ue_is_valid(self.Presentation) && ue_is_valid(self.Presentation.CharacterMesh)) {
            rogue_apply_mesh(self.Mesh, self.Presentation)
            self.Visual.SetHiddenInGame(true, false)
            self.UsingExternalPresentation = true
        }
        self.ActionSystem.SetBaseMoveSpeed(self.WalkSpeed)
        if (ue_class_valid(self.SprintActionClass)) {
            self.ActionSystem.GrantAction(self.SprintActionClass)
        }
        if (ue_class_valid(self.AttackActionClass)) {
            let action = self.ActionSystem.GrantAction(self.AttackActionClass)
            if (ue_is_valid(action) && ue_is_valid(self.Presentation)) {
                rogue_apply_attack(ue_ref(type<RogueProjectileAttackRef>, action.handle), self.Presentation)
            }
        }
        self.CharacterMovement.JumpZVelocity = self.JumpVelocity
        self.CharacterMovement.AirControl = self.AirControl
        self.CharacterMovement.bOrientRotationToMovement = true
        self.CharacterMovement.RotationRate = ue_rotator(0.0lf, 540.0lf, 0.0lf)
        // Visual geometry never contributes collision; the native capsule does.
        self.Visual.SetCollisionProfileName(ue_name_value("NoCollision"), true)
        // The placeholder visual has no skeletal hit mesh; use the capsule.
        self.CapsuleComponent.SetCollisionResponseToChannel(ECollisionChannel.ECC_GameTraceChannel2, ECollisionResponse.ECR_Block)
        self.RefreshHealth()
        self.TryBindControls()
    }

    def Tick(delta : float) : void {
        if (!self.Dead && !self.ControlsBound) { self.TryBindControls() }
        self.FaceHealthLabel()
    }

    def TryBindControls() : void {
        if (self.Dead) { return }
        let pawn = ue_character_self()
        if (!ue_character_controls_ready(pawn)) { return }
        ue_enhanced_add_context(ue_pawn_controller(pawn), self.Controls, 1)
        ue_bind_inputs()
        self.ControlsBound = true
    }

    [ue_input(action="Input_Sprint", Started, Completed, Canceled)]
    def OnSprint(value : bool) : void {
        if (self.Dead) { return }
        if (value) { self.ActionSystem.StartAction(ue_tag("Action.Sprint")) }
        else { self.ActionSystem.StopAction(ue_tag("Action.Sprint")) }
    }

    [ue_input(action="Input_Move", Triggered)]
    def OnMove(value : InputActionValue) : void {
        if (self.Dead) { return }
        let axis = ue_input_axis2d(value)
        let player = ue_pawn_controller(ue_character_self())
        let yawRotation = ue_rotator(0.0lf, player.GetControlRotation().yaw, 0.0lf)
        self.MoveEvents += 1
        self.AddMovementInput(ue_rotate_vector(yawRotation, UE_VECTOR_FORWARD), float(axis.x))
        self.AddMovementInput(ue_rotate_vector(yawRotation, UE_VECTOR_RIGHT), float(axis.y))
    }

    [ue_input(action="Input_Look", Triggered)]
    def OnLook(value : InputActionValue) : void {
        if (self.Dead) { return }
        let axis = ue_input_axis2d(value)
        self.LookEvents += 1
        self.AddControllerYawInput(float(axis.x))
        self.AddControllerPitchInput(float(axis.y))
    }

    [ue_input(action="Input_Jump", Started, Completed, Canceled)]
    def OnJump(value : bool) : void {
        if (self.Dead) { return }
        if (value) {
            self.JumpPresses += 1
            self.Jump()
        }
        else {
            self.JumpReleases += 1
            self.StopJumping()
        }
    }

    [ue_function(BlueprintPure)]
    def IsAlive() : bool { return !self.Dead && self.Attributes.IsAlive() }

    [ue_input(action="Input_TestDamage", Started)]
    def OnTestDamage(value : bool) : void {
        if (!value || self.Dead) { return }
        ue_apply_damage(ue_self_actor(), self.TestDamage, ue_self_actor(), ue_pawn_controller(ue_character_self()))
    }

    def BindEvents() : void {
        self.Attributes.OnHealthChanged += self.HandleHealthChanged
    }

    def HandleHealthChanged(instigator : ActorRef; health : float; delta : float) : void {
        self.OnHealthChanged(instigator, health, delta)
    }

    [ue_function(BlueprintCallable)]
    def OnHealthChanged(instigator : ActorRef; health : float; delta : float) : void {
        if (health <= 0.0f && !self.Dead) {
            self.Dead = true
            self.DeathCount += 1
            self.ActionSystem.Shutdown()
            if (ue_is_valid(self.Presentation) && ue_is_valid(self.Presentation.DeathMontage)) {
                ue_character_play_montage(ue_character_self(), self.Presentation.DeathMontage)
            }
            self.StopJumping()
            self.CharacterMovement.StopMovementImmediately()
            self.CharacterMovement.DisableMovement()
            let player = ue_pawn_controller(ue_character_self())
            if (ue_object_valid(player.handle)) {
                player.SetIgnoreMoveInput(true)
                player.SetIgnoreLookInput(true)
                self.DisableInput(player)
                player.DisableInput(player)
            }
        }
        self.RefreshHealth()
    }

    def RefreshHealth() : void {
        if (self.Dead) { self.HealthLabel.K2_SetText(ue_text_invariant("DEAD - restart Play")) }
        else { self.HealthLabel.K2_SetText(ue_text_invariant("HP: {int(self.Attributes.Health)} / {int(self.Attributes.HealthMax)}")) }
    }

    def FaceHealthLabel() : void {
        let location = self.HealthLabel.K2_GetComponentLocation()
        let camera = self.CameraComponent.K2_GetComponentLocation()
        let rotation = ue_direction_rotation(camera - location)
        ue_scene_set_world_transform(ue_ref(type<SceneComponentRef>, self.HealthLabel.handle),
            ue_transform(location, rotation, UE_VECTOR_ONE))
    }
}
