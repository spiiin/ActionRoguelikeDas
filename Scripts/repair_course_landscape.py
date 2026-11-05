"""Replace only the imported course terrain with the original merged surface."""
from pathlib import Path
import datetime,re,shutil
import unreal

ROOT=Path(__file__).resolve().parents[1]
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
assert editor.get_game_world() is None,'Stop PIE before repairing terrain'
world=editor.get_editor_world()
assert world and world.get_name()=='P_OpenWorldTestMap_Das'
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
text=(ROOT/'Saved/ExternalAssets/course_world/native_geometry.t3d').read_text()
blocks=[m[0] for m in re.finditer(r'^[ \t]*Begin Actor\b.*?^[ \t]*End Actor[ \t]*(?:\n|$)',text,re.M|re.S)
        if '/Script/Landscape.' in m[0].splitlines()[0]]
assert len(blocks)==65
assert all('LayersData=' not in b and 'LandscapeEditLayers(' not in b for b in blocks),'Run the updated course installer first'
source=ROOT/'Saved/ExternalAssets/course_world/landscape_geometry.t3d'
source.write_text('Begin Map\nBegin Level\n'+''.join(blocks)+'End Level\nEnd Map\n',newline='\n')
backup=ROOT/'Saved/Backups'/('Landscape-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir(parents=True,exist_ok=False)
shutil.copy2(ROOT/'Content/DasRogueExternal/Maps/P_OpenWorldTestMap_Das.umap',backup/'P_OpenWorldTestMap_Das.umap')
old=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
assert len(old)==65,len(old)
# Proxies first, then their root; leave all gameplay and other geometry untouched.
old.sort(key=lambda a:isinstance(a,unreal.Landscape))
for actor in old:assert actors.destroy_actor(actor),actor.get_name()
unreal.SystemLibrary.execute_console_command(world,'Das.World.ImportText '+str(source).replace('\\','/'))
assert assets.get_metadata_tag(world,'DasWorldImportComplete')=='1'
terrain=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
assert len(terrain)==65,len(terrain)
assets.set_metadata_tag(world,'DasCourseGeometry','6')
print('DAS_COURSE_LANDSCAPE_REPAIRED',len(terrain),'actors; backup',backup)
