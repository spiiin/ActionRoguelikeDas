"""Import DAS abilities and extend controller mappings without discarding overrides."""
from pathlib import Path
import json
import runpy
import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assets = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
unreal.SystemLibrary.execute_console_command(world,
    'Das.DSL.Interfaces.Apply rogue_projectile_impact_interface.das /Game/DasRogue/Types')

def apply(source, path, identity):
    command = ('Das.DSL.Reimport ' + path if assets.does_asset_exist(path)
        else f'Das.DSL.Apply {source}.das {path} {identity}')
    unreal.SystemLibrary.execute_console_command(world, command)
    blueprint = unreal.load_asset(path)
    assert blueprint, path
    assert unreal.EditorLoadingAndSavingUtils.save_packages([blueprint.get_outer()], False), path

for name in ['IA_SecondaryAttack', 'IA_SpecialAttack']:
    path = '/Game/DasRogue/Input/' + name
    action = unreal.load_asset(path) if assets.does_asset_exist(path) else tools.create_asset(
        name, '/Game/DasRogue/Input', unreal.InputAction, unreal.InputAction_Factory())
    assert action
    action.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
    assert unreal.EditorLoadingAndSavingUtils.save_packages([action.get_outer()], False)

for source, path, identity in [
    ('rogue_projectile', '/Game/DasRogue/BP_RogueProjectile', 'rogue.RogueProjectile'),
    ('rogue_presentation_profile', '/Game/DasRogue/Types/BP_RoguePresentationProfile', 'rogue.RoguePresentationProfile'),
    ('rogue_projectile_blackhole', '/Game/DasRogue/Projectiles/BP_RogueProjectileBlackhole', 'rogue.RogueProjectileBlackhole'),
    ('rogue_blackhole_attack_projectile', '/Game/DasRogue/Projectiles/BP_BlackholeAttackProjectile', 'roguedemo.RogueBlackholeAttackProjectile'),
    ('rogue_projectile_teleport', '/Game/DasRogue/Projectiles/BP_RogueProjectileTeleport', 'rogue.RogueProjectileTeleport'),
    ('rogue_teleport_demo', '/Game/DasRogue/Projectiles/BP_TeleportDemo', 'roguedemo.RogueTeleportDemo'),
    ('rogue_action_blackhole', '/Game/DasRogue/Actions/BP_RogueActionBlackhole', 'rogue.RogueActionBlackhole'),
    ('rogue_action_teleport', '/Game/DasRogue/Actions/BP_RogueActionTeleport', 'rogue.RogueActionTeleport'),
    ('rogue_teleport_probe', '/Game/DasRogue/Tests/BP_RogueTeleportProbe', 'roguetest.RogueTeleportProbe'),
]:
    apply(source, path, identity)

runpy.run_path(str(Path(__file__).with_name('prepare_character.py')))
# Optional licensed presentation stays in the ignored local profile. Keep the
# native MetaSound graphs out of the dependency set; use the acquired waves.
root = Path(__file__).resolve().parents[1]
profile_path = '/Game/DasRogueExternal/DA_Presentation'
if assets.does_asset_exist(profile_path):
    profile = unreal.load_asset(profile_path)
    manifest = json.loads((root / 'ExternalAssets.json').read_text())
    for name in ['BlackholeEffect', 'BlackholeSound', 'TeleportImpactEffect', 'TeleportImpactSound']:
        path = manifest['course_effects'][name]
        if (root / 'Content' / (path.removeprefix('/Game/') + '.uasset')).is_file():
            resource = unreal.load_asset(path)
            assert resource, path
            profile.modify(True)
            profile.set_editor_property(name, resource)
mapping = unreal.load_asset('/Game/DasRogue/Input/IMC_Rogue')
mapping.modify(True)
for name, key_name in [('IA_SecondaryAttack', 'F'), ('IA_SpecialAttack', 'Q')]:
    action = unreal.load_asset('/Game/DasRogue/Input/' + name)
    entries = mapping.get_editor_property('default_key_mappings').get_editor_property('mappings')
    if any(entry.get_editor_property('action') == action for entry in entries):
        continue
    key = unreal.Key()
    key.set_editor_property('key_name', key_name)
    mapping.map_key(action, key)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
unreal.log('DAS_ADDITIONAL_ATTACKS_PREPARED')
