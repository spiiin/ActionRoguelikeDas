"""Install locally acquired scene resources and prepare native geometry for editor import.
No JSON is read by gameplay. All generated files remain in ignored local folders.
"""
import argparse,hashlib,json,re,shutil,subprocess
from pathlib import Path
from setup_external_assets import ROOT,MANIFEST,dependencies
from course_landscape import bake_landscape_scene, surface_samples

TARGET='/Game/DasRogueExternal/Maps/P_OpenWorldTestMap_Das'

def install(source,reference=None):
    source=Path(source).resolve(strict=True)
    reference=Path(reference or ROOT/'Saved/Tests/original_world').resolve(strict=True)
    data=json.loads((reference/'reference.json').read_text())
    assert data['passed']
    out=ROOT/'Saved/ExternalAssets/course_world';out.mkdir(parents=True,exist_ok=True)
    original=data['source']+'.'+data['source'].rsplit('/',1)[-1]
    target=TARGET+'.'+TARGET.rsplit('/',1)[-1]
    native=(reference/'native_geometry.t3d').read_text()
    # Native Landscape proxies opt out of clipboard selection. Their full object
    # export includes TextureSourceData; retain those bytes and all 64 actor poses.
    proxies=[]
    terrain_samples=[]
    for actor in data['actors']:
        if actor['kind']!='/Script/Landscape.LandscapeStreamingProxy':continue
        text=(reference/(actor['name']+'.t3d')).read_text()
        terrain_samples.extend(dict(sample,actor=actor['label']) for sample in surface_samples(text,actor['components']))
        lines=text.splitlines(keepends=True)
        lines[0]=lines[0].replace("Begin Object", "Begin Actor", 1)
        for index in range(len(lines)-1,-1,-1):
            if lines[index].strip()=='End Object':
                lines[index]='End Actor\n';break
        proxies.append(''.join(lines))
    assert len(proxies)==64
    assert len(terrain_samples)==256
    (out/'landscape_surface_reference.json').write_text(json.dumps(terrain_samples,indent=2),newline='\n')
    marker=native.rfind('End Level')
    assert marker>=0
    native=native[:marker]+''.join(proxies)+native[marker:]
    native=bake_landscape_scene(native)
    native=native.replace(original,target).replace(data['source'],TARGET)
    assert '/Script/ActionRoguelike.' not in native
    (out/'native_geometry.t3d').write_text(native,newline='\n')
    query=(reference/'spawn_query.t3d').read_text().replace(
        "/Script/CoreUObject.Class'/Script/ActionRoguelike.URogueEnvQueryContext_AlivePlayers'",
        "/Script/Engine.BlueprintGeneratedClass'/Game/DasRogue/AI/BT/BP_RogueEQSAlivePlayers.BP_RogueEQSAlivePlayers_C'")
    (out/'spawn_query.t3d').write_text(query,newline='\n')
    for index,config in enumerate(data['directors']):
        (out/f'income_{index}.txt').write_text(config['curve_text'],newline='\n')
    (out/'layout.json').write_text(json.dumps(data,indent=2),newline='\n')
    config=json.loads(MANIFEST.read_text())
    allowed=set(config['allowed_roots'])
    paths=set(re.findall(r'/Game/[A-Za-z0-9_/-]+',native))
    paths.update(value.split('.')[0] for value in config.get('course_coins',{}).values() if value.startswith('/Game/'))
    paths.update(value.split('.')[0] for value in config.get('course_world_effects',{}).values())
    paths.update(config.get('course_ui',{}).values())
    for actor in data['actors']:
        paths.update(v.split('.')[0] for v in actor.get('properties',{}).values() if isinstance(v,str) and v.startswith('/Game/'))
        for component in actor['components']:
            paths.update(component[k].split('.')[0] for k in ['asset','sound'] if component.get(k))
            if component.get('mesh'):paths.add(component['mesh'].split('.')[0])
            paths.update(p.split('.')[0] for p in component.get('materials',[]) if p)
    visited=set();copied=[];missing=[]
    while paths:
        package=paths.pop().split('.')[0]
        if package in visited:continue
        visited.add(package)
        rel=Path(package.removeprefix('/Game/'))
        if rel.is_absolute() or '..' in rel.parts:raise ValueError(package)
        if not rel.parts or rel.parts[0] not in allowed:continue
        src=(source/rel).with_suffix('.uasset')
        if not src.is_file():missing.append(package);continue
        raw=src.read_bytes();paths.update(dependencies(raw)-visited)
        dest=(ROOT/'Content'/rel).with_suffix('.uasset')
        if subprocess.run(['git','-C',str(ROOT),'check-ignore','--quiet',str(dest)]).returncode:
            raise RuntimeError('Scene resources must stay gitignored: '+str(dest))
        dest.parent.mkdir(parents=True,exist_ok=True)
        digest=hashlib.sha256(raw).hexdigest()
        if not dest.is_file() or hashlib.sha256(dest.read_bytes()).hexdigest()!=digest:shutil.copy2(src,dest)
        copied.append(str(rel.with_suffix('.uasset')).replace('\\','/'))
    receipt=dict(source_content=str(source),source_revision=config['source']['revision'],target=TARGET,landscape_proxies=len(proxies),geometry_version=6,landscape_mode="merged_source_heightmaps",files=sorted(copied),missing=sorted(missing))
    (out/'install.json').write_text(json.dumps(receipt,indent=2))
    print('DAS_COURSE_WORLD_INSTALL',len(copied),'files,',len(proxies),'landscape proxies')
    return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-content',type=Path,required=True)
    parser.add_argument('--reference',type=Path)
    args=parser.parse_args();install(args.source_content,args.reference)
