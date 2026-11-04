from pathlib import Path
"""Migrate authored projectile parents before any demo/attack subclasses."""
import unreal
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
__import__('runpy').run_path(str(Path(__file__).resolve().with_name('prepare_burning_effect.py')))
registry=unreal.AssetRegistryHelpers.get_asset_registry()
unreal.SystemLibrary.execute_console_command(world,
    'Das.DSL.Interfaces.Apply rogue_projectile_impact_interface.das /Game/DasRogue/Types')
for source,name in [('rogue_projectile.das','RogueProjectile'),('rogue_magic_projectile.das','RogueMagicProjectile')]:
    paths={str(asset.package_name) for asset in registry.get_assets_by_path('/Game/DasRogue',recursive=True) if str(asset.asset_name)=='BP_'+name}
    paths.add('/Game/DasRogue/BP_'+name)
    for path in sorted(paths):
        command=('Das.DSL.Reimport '+path if unreal.load_asset(path)
            else f'Das.DSL.Apply {source} {path} rogue.{name}')
        unreal.SystemLibrary.execute_console_command(world,command)
