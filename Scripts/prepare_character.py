"""Idempotent editor setup. Runtime behavior is entirely in rogue_character.das."""
import unreal
from pathlib import Path
__import__('runpy').run_path(str(Path(__file__).resolve().with_name('prepare_attribute_sets.py')))

tools=unreal.AssetToolsHelpers.get_asset_tools()
def asset(name,cls,factory):
    value=unreal.load_asset('/Game/DasRogue/Input/'+name)
    if not value:
        value=tools.create_asset(name,'/Game/DasRogue/Input',cls,factory())
    assert value, name
    value.modify(True)
    return value

move=asset('IA_Move',unreal.InputAction,unreal.InputAction_Factory)
look=asset('IA_Look',unreal.InputAction,unreal.InputAction_Factory)
jump=asset('IA_Jump',unreal.InputAction,unreal.InputAction_Factory)
sprint=asset('IA_Sprint',unreal.InputAction,unreal.InputAction_Factory)
sprint.set_editor_property('value_type',unreal.InputActionValueType.BOOLEAN)
hurt=asset('IA_TestDamage',unreal.InputAction,unreal.InputAction_Factory)
hurt.set_editor_property('value_type',unreal.InputActionValueType.BOOLEAN)
move.set_editor_property('value_type',unreal.InputActionValueType.AXIS2D)
look.set_editor_property('value_type',unreal.InputActionValueType.AXIS2D)
jump.set_editor_property('value_type',unreal.InputActionValueType.BOOLEAN)
mapping=asset('IMC_Character',unreal.InputMappingContext,unreal.InputMappingContext_Factory)
mapping.unmap_all()
entries=[]
def key(action,name,negate=False,swizzle=False):
    k=unreal.Key()
    k.set_editor_property('key_name',name)
    entry=mapping.map_key(action,k)
    mods=[]
    if negate: mods.append(unreal.new_object(unreal.InputModifierNegate,outer=mapping))
    if swizzle:
        mod=unreal.new_object(unreal.InputModifierSwizzleAxis,outer=mapping)
        mod.set_editor_property('order',unreal.InputAxisSwizzle.YXZ)
        mods.append(mod)
    entry.set_editor_property('modifiers',mods)
    entries.append(entry)
    return entry
# Original Move uses X=forward and Y=right.
key(move,'W');key(move,'S',negate=True)
key(move,'D',swizzle=True);key(move,'A',negate=True,swizzle=True)
key(look,'MouseX');key(look,'MouseY',negate=True,swizzle=True)
key(jump,'SpaceBar')
key(hurt,'H')
key(sprint,'LeftShift')
# map_key returns a Python struct copy. Persist the modified entries explicitly.
data=mapping.get_editor_property('default_key_mappings')
data.set_editor_property('mappings',entries)
mapping.set_editor_property('default_key_mappings',data)
saved=mapping.get_editor_property('default_key_mappings').get_editor_property('mappings')
assert len(saved)==9
assert [m.get_class().get_name() for m in saved[1].get_editor_property('modifiers')]==['InputModifierNegate']
assert len(saved[3].get_editor_property('modifiers'))==2
assert unreal.EditorLoadingAndSavingUtils.save_packages([x.get_outer() for x in [move,look,jump,hurt,sprint,mapping]],False)
migration_source=Path(__file__).resolve().parents[1]/'Content/Das/Scripts/rogue/rogue_player_controller.das'
migration_backup=Path(__file__).resolve().parents[1]/'Saved/Migrations/rogue_player_controller.final.das'
stage_marker='// DAS_INPUT_FIELD_ARCHIVE_STAGE\n'
if migration_backup.exists() and migration_source.read_text(encoding='utf-8-sig').startswith(stage_marker):
    migration_source.write_bytes(migration_backup.read_bytes())
    migration_backup.unlink()
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_presentation_profile.das /Game/DasRogue/Types/BP_RoguePresentationProfile rogue.RoguePresentationProfile')
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_attribute_component.das /Game/DasRogue/BP_RogueAttributeComponent rogue.RogueAttributeComponent')
for command in [
    'Das.DSL.Interfaces.Apply rogue_action_host_interface.das /Game/DasRogue/Types',
    'Das.DSL.Apply rogue_action.das /Game/DasRogue/Actions/BP_RogueAction rogue.RogueAction',
    'Das.DSL.Apply rogue_action_sprint.das /Game/DasRogue/Actions/BP_RogueActionSprint rogue.RogueActionSprint',
    'Das.DSL.Apply rogue_action_projectile_attack.das /Game/DasRogue/Actions/BP_RogueActionProjectileAttack rogue.RogueActionProjectileAttack',
    'Das.DSL.Apply rogue_action_system_component.das /Game/DasRogue/BP_RogueActionSystemComponent rogue.RogueActionSystemComponent',
    'Das.DSL.Apply rogue_action_effect.das /Game/DasRogue/Actions/BP_RogueActionEffect rogue.RogueActionEffect',
    'Das.DSL.Apply rogue_action_effect_stun.das /Game/DasRogue/Actions/BP_RogueActionEffectStun rogue.RogueActionEffectStun',
    'Das.DSL.Apply rogue_action_effect_overwhelm.das /Game/DasRogue/Actions/BP_RogueActionEffectOverwhelm rogue.RogueActionEffectOverwhelm',
]:
    if command.startswith('Das.DSL.Apply rogue_action_system_component.das '):
        # Migrate only the legacy bootstrap's exact CDO override. Gameplay configuration now lives in DAS.
        legacy_sprint=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionSprint.BP_RogueActionSprint_C')
        component_kind=unreal.load_class(None,'/Game/DasRogue/BP_RogueActionSystemComponent.BP_RogueActionSystemComponent_C')
        character_kind=unreal.load_class(None,'/Game/DasRogue/BP_RogueCharacter.BP_RogueCharacter_C')
        candidates=[]
        if component_kind:candidates.append(unreal.get_default_object(component_kind))
        if character_kind:candidates.append(unreal.get_default_object(character_kind).get_editor_property('ActionSystem'))
        for target in candidates:
            if target and list(target.get_editor_property('DefaultActions'))==[legacy_sprint]:
                target.modify(True)
                target.set_editor_property('DefaultActions',[])
    # Merge the original 5000 cm aim default without replacing manual overrides.
    if command.startswith('Das.DSL.Apply rogue_action_projectile_attack.das ') and unreal.load_asset('/Game/DasRogue/Actions/BP_RogueActionProjectileAttack'):
        command='Das.DSL.Reimport /Game/DasRogue/Actions/BP_RogueActionProjectileAttack defaults=preserve_overrides'
    unreal.SystemLibrary.execute_console_command(world,command)
    if command.startswith('Das.DSL.Interfaces.Apply'):
        interface=unreal.load_asset('/Game/DasRogue/Types/RogueActionHost')
        assert interface and unreal.load_class(None,'/Game/DasRogue/Types/RogueActionHost.RogueActionHost_C')
        unreal.EditorLoadingAndSavingUtils.save_packages([interface.get_outer()],False)
action_system=unreal.load_asset('/Game/DasRogue/BP_RogueActionSystemComponent')
sprint_class=unreal.load_class(None,'/Game/DasRogue/Actions/BP_RogueActionSprint.BP_RogueActionSprint_C')
assert action_system and sprint_class, 'Action system import failed; inspect log'
action_system.modify(True)
# SprintActionClass and granting the default action are authored in rogue_character.das.
unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_character.das /Game/DasRogue/BP_RogueCharacter rogue.RogueCharacter')
controller=unreal.load_asset('/Game/DasRogue/BP_RoguePlayerController')
if controller:
    # Archive only the known obsolete bootstrap/input flags, preserving dependent packages.
    removed_fields=('ProjectileClass','FireBound')
    def has_field(name):
        try:
            unreal.get_default_object(controller.generated_class()).get_editor_property(name)
            return True
        except Exception:
            return False
    # Field archival requires a removal-only declaration. Stage the previous
    # callback shape without obsolete fields, then apply the new setup event.
    if any(has_field(name) for name in removed_fields):
        source_path=Path(__file__).resolve().parents[1]/'Content/Das/Scripts/rogue/rogue_player_controller.das'
        final_bytes=source_path.read_bytes()
        final_source=final_bytes.decode('utf-8-sig').replace('\r\n','\n')
        stage=final_source.replace('        var InputSetups : int = 0\n','')
        stage=stage.replace('        ue_controller_set_team(ue_ref(type<PlayerControllerRef>, ue_self_object()), self.TeamId)\n',
            '        ue_controller_set_team(ue_ref(type<PlayerControllerRef>, ue_self_object()), self.TeamId)\n        self.TryBindControls()\n')
        start=stage.index('    [ue_function(BlueprintEvent)]\n    def SetupInputComponent()')
        end=stage.index('    [ue_input(action="Input_Fire"',start)
        stage=stage[:start]+'''    def Tick(delta : float) : void {
        if (!self.ControlsBound) { self.TryBindControls() }
    }

    def TryBindControls() : void {
        let player = ue_ref(type<PlayerControllerRef>, ue_self_object())
        let hasInputs = ue_is_valid(self.Controls) && ue_is_valid(self.Input_Interact) && ue_is_valid(self.Input_Fire)
        if (!hasInputs || !ue_player_controls_ready(player) || self.ControlsBound) { return }
        ue_enhanced_add_context(player, self.Controls, 0)
        ue_bind_inputs()
        self.ControlsBound = true
    }

'''+stage[end:]
        try:
            migration_backup.parent.mkdir(parents=True,exist_ok=True)
            migration_backup.write_bytes(final_bytes)
            source_path.write_text(stage_marker+stage,encoding='utf-8')
            unreal.SystemLibrary.execute_console_command(world,
                'Das.DSL.Reimport /Game/DasRogue/BP_RoguePlayerController fields=archive_remove_with_dependencies')
            if any(has_field(name) for name in removed_fields):
                raise RuntimeError('Controller field archival failed; inspect DAS_DSL_ARCHIVE in the log')
        finally:
            source_path.write_bytes(final_bytes)
            migration_backup.unlink(missing_ok=True)
    unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Reimport /Game/DasRogue/BP_RoguePlayerController')
    unreal.get_default_object(controller.generated_class()).get_editor_property('InputSetups')

else:
    unreal.SystemLibrary.execute_console_command(world,'Das.DSL.Apply rogue_player_controller.das /Game/DasRogue/BP_RoguePlayerController rogue.RoguePlayerController')
kind=unreal.load_class(None,'/Game/DasRogue/BP_RogueCharacter.BP_RogueCharacter_C')
assert kind, 'Character import failed; inspect log'
try:
    unreal.get_default_object(kind).get_editor_property('Presentation')
except Exception as error:
    raise RuntimeError('New Character declaration failed to apply; inspect DAS_DSL_APPLY') from error
game=unreal.load_asset('/Game/DasRogue/BP_RogueGameMode')
game.modify(True)
game_class=unreal.load_class(None,'/Game/DasRogue/BP_RogueGameMode.BP_RogueGameMode_C')
unreal.get_default_object(game_class).set_editor_property('default_pawn_class',kind)
unreal.BlueprintEditorLibrary.compile_blueprint(game)
assert unreal.get_default_object(game.generated_class()).get_editor_property('default_pawn_class')==kind
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
print('DAS_CHARACTER_PREPARE PASS',kind.get_path_name())
