options gen2
module rogue_action_projectile_attack public
require rogue_action public
require ue_animation public
require ue_effects public
require ue_vector_math public

// Adapted from Tom Looman's RogueAction_ProjectileAttack, commit 992f860.
// Publication permission and redistribution license are pending.
[ue_class(module_id="rogue", Blueprintable)]
class RogueActionProjectileAttack : RogueAction {

    settings = ue_properties(EditAnywhere, BlueprintReadWrite, Category = "Attack") {
        var ProjectileClass : ActorClass
        var AttackDelay : float = 0.2f
        var AttackMontage : AnimMontageRef
        var CastingEffect : NiagaraSystemRef
        var CastingSound : SoundBaseRef
        var MuzzleSocketName : string = "Muzzle_01"
        // Fallback for characters without a skeletal mesh/socket, including the cone test pawn.
        var MuzzleOffset : float = 75.0f
        var MuzzleHeight : float = 40.0f
        var AimDistance : float = 10000.0f
        var MuzzleClearance : float = 16.0f
    }

    state = ue_properties(BlueprintReadWrite) {
        var ProjectilesFired : int = 0
        var LastProjectile : ActorRef
        var LastMuzzleLocation : UEVector
        var LastAimPoint : UEVector
        var BlockedShots : int = 0
    }

    defaults = ue_defaults() {
        self.ProjectileClass = ue_class_default("/Game/DasRogue/BP_MagicProjectileDemo.BP_MagicProjectileDemo_C")
        self.CooldownTime = 0.5f
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override Setup() : void {
        Super.Setup()
        if (!ue_tag_valid(self.ActionName)) { self.ActionName = ue_tag("Action.PrimaryAttack") }
        if (ue_tags_count(self.BlockedTags) == 0) { self.BlockedTags = ue_tags(ue_tag("StatusEffect.Stunned")) }
    }

    def GetPawn() : NativePawnRef {
        return ue_ref(type<NativePawnRef>, ue_component_owner(ue_object_outer(ue_self_object())))
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override StartAction() : void {
        Super.StartAction()
        let pawn = self.GetPawn()
        if (!ue_object_valid(pawn.handle) || !ue_class_valid(self.ProjectileClass)) {
            self.StopAction()
            return
        }
        if (ue_object_is_a(pawn.handle, "/Script/Engine.Character") && ue_is_valid(self.AttackMontage)) {
            ue_character_play_montage(ue_ref(type<CharacterRef>, pawn.handle), self.AttackMontage)
        }
        if (ue_is_valid(self.CastingSound)) { ue_sound_play_2d(self.CastingSound) }
        if (ue_is_valid(self.CastingEffect)) {
            var component = ue_ref(type<ActorRef>, pawn.handle).RootComponent
            if (ue_object_is_a(pawn.handle, "/Script/Engine.Character")) {
                let mesh = ue_ref(type<CharacterRef>, pawn.handle).Mesh
                component = ue_ref(type<SceneComponentRef>, mesh.handle)
            }
            ue_niagara_spawn_attached(self.CastingEffect, component, ue_name_value(self.MuzzleSocketName))
        }
        ue_timer_start("Attack", self.AttackDelay, self.AttackTimerElapsed, false)
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override StopAction() : void {
        ue_timer_cancel("Attack")
        Super.StopAction()
    }

    [ue_function]
    def AttackTimerElapsed() : void {
        if (!self.bIsRunning) { return }
        if (ue_object_valid(self.Host.handle) && self.Host.IsActionOwnerAlive()) { self.FireProjectile() }
        self.StopAction()
    }

    def FireProjectile() : void {
        let pawn = self.GetPawn()
        if (!ue_object_valid(pawn.handle)) { return }
        let player = ue_pawn_controller(pawn)
        if (!ue_object_valid(player.handle)) { return }
        var camera = UE_VECTOR_ZERO
        var rotation = UE_ROTATOR_ZERO
        player.GetPlayerViewPoint(camera, rotation)
        let forward = ue_rotate_vector(rotation, UE_VECTOR_FORWARD)
        let finish = camera + forward * double(self.AimDistance)
        var ignored <- [ue_ref(type<ActorRef>, pawn.handle)]
        let aim = ue_line_trace(camera, finish, ignored)
        let target = aim.blocking_hit ? aim.impact_point : finish
        let origin = ue_ref(type<ActorRef>, pawn.handle).K2_GetActorLocation()
        let base = origin + UE_VECTOR_UP * double(self.MuzzleHeight)
        let yawRotation = ue_rotator(0.0lf, rotation.yaw, 0.0lf)
        let muzzleForward = ue_rotate_vector(yawRotation, UE_VECTOR_FORWARD)
        var position = base + muzzleForward * double(self.MuzzleOffset)
        if (ue_object_is_a(pawn.handle, "/Script/Engine.Character")) {
            let mesh = ue_ref(type<CharacterRef>, pawn.handle).Mesh
            let scene = ue_ref(type<SceneComponentRef>, mesh.handle)
            let socket = ue_name_value(self.MuzzleSocketName)
            if (ue_is_valid(scene) && scene.DoesSocketExist(socket)) { position = scene.GetSocketLocation(socket) }
        }
        // Clip the muzzle to the near side of cover, never spawn through it.
        let cover = ue_sphere_trace(base, position, double(self.MuzzleClearance), ignored)
        if (cover.start_penetrating) {
            self.BlockedShots += 1
            return
        }
        if (cover.blocking_hit) {
            position = cover.location + cover.normal
        }
        let direction = target - position
        // Camera-only targets behind the muzzle cannot be shot forwards.
        if (dot(direction, forward) <= 1.0lf) {
            self.BlockedShots += 1
            return
        }
        let pose = ue_transform(position, ue_direction_rotation(direction), UE_VECTOR_ONE)
        self.LastMuzzleLocation = position
        self.LastAimPoint = target
        self.LastProjectile = ue_actor_spawn(type<ActorRef>, self.ProjectileClass, pose,
            ue_ref(type<ActorRef>, player.handle), "AlwaysSpawn", pawn)
        if (ue_object_valid(self.LastProjectile.handle)) { self.ProjectilesFired += 1 }
    }
}
