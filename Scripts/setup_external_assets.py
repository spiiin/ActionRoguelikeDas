"""Install already acquired course resources, keeping all licensed files outside Git.

Download/acquire resources from their publishers under their own terms first.
The UE5.6 course profile uses Manny-retargeted Gideon animations; the raw Fab
Gideon pack alone does not contain these exact retargeted assets.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import webbrowser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'ExternalAssets.json'

def run(*args):
    subprocess.run(args,check=True)

def dependencies(data):
    # Unreal package names are UTF-8 names; also cover wide serialized soft paths.
    found=set(x.decode('ascii') for x in re.findall(rb'/Game/[A-Za-z0-9_/-]+',data))
    found.update(re.findall(r'/Game/[A-Za-z0-9_/-]+',data.decode('utf-16-le',errors='ignore')))
    return found

def install(source,with_effects=False,with_minions=False,with_course_animation=False):
    config=json.loads(MANIFEST.read_text(encoding='utf-8'))
    source=Path(source).resolve(strict=True)
    if source.name!='Content':raise ValueError('Pass the source project Content directory')
    assets=dict(config['assets'])
    if with_effects:assets.update(config['course_effects'])
    if with_course_animation:assets['CharacterMesh']=config['course_animation']['CharacterMesh']
    ai_assets=dict(config.get('ai_assets',{})) if with_minions else {}
    allowed=set(config['allowed_roots'])
    ignored=set(config['excluded_assets'])
    todo=list(assets.values())+list(ai_assets.values())
    if with_course_animation:todo.append(config['course_animation']['source_blueprint'])
    visited=set(); files=[]; missing=[]
    while todo:
        package=todo.pop()
        if package in visited:continue
        visited.add(package)
        relative=Path(package.removeprefix('/Game/'))
        if relative.is_absolute() or '..' in relative.parts:raise ValueError(package)
        if relative.parts[0] not in allowed:continue
        path=(source/relative).with_suffix('.uasset')
        if not path.is_file():
            # Packages can retain old retarget-source/preview paths. Record them;
            # Unreal's dependency and runtime checks verify the actual load graph.
            missing.append(package);continue
        data=path.read_bytes()
        if relative.name not in ignored:
            files.append((path,relative.with_suffix('.uasset'),hashlib.sha256(data).hexdigest()))
        todo.extend(dependencies(data)-visited)
    seeds=[p for p in list(assets.values())+list(ai_assets.values()) if not (source/Path(p.removeprefix('/Game/'))).with_suffix('.uasset').is_file()]
    if seeds:raise FileNotFoundError('Required assets missing: '+repr(seeds))
    # Never copy content unless the destination patterns already protect it.
    for name in allowed|{'DasRogueExternal'}:
        probe=ROOT/'Content'/name/'license_probe.uasset'
        result=subprocess.run(['git','-C',str(ROOT),'check-ignore','--quiet',str(probe)])
        if result.returncode:raise RuntimeError('External content must be gitignored before installation: '+name)
    for path,relative,digest in files:
        target=ROOT/'Content'/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
            shutil.copy2(path,target)
    receipt={'source_content':str(source),'source_revision':config['source']['revision'],
        'assets':assets,'ai_assets':ai_assets,'course_effects':with_effects,'minions':with_minions,'course_animation':with_course_animation,'files':[str(r).replace('\\','/') for _,r,_ in files],
        'sha256':{str(r).replace('\\','/'):h for _,r,h in files},'unresolved_preview_or_source_paths':sorted(missing)}
    dest=ROOT/'Saved/ExternalAssets/install.json';dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(f'Installed {len(files)} licensed files locally; receipt: {dest}')
    return receipt

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-content',type=Path)
    parser.add_argument('--with-course-effects',action='store_true',help='Use locally acquired tharlevfx Niagara and Sander audio too')
    parser.add_argument('--with-course-animation',action='store_true',help='Install original player Anim Blueprint dependencies; then run export_course_animation.py in the source editor')
    parser.add_argument('--with-minions',action='store_true',help='Also install the ranged Paragon Minion dependency graph')
    parser.add_argument('--open-sources',action='store_true',help='Open the official Fab listing and course resource instructions')
    args=parser.parse_args()
    if args.open_sources:
        config=json.loads(MANIFEST.read_text())
        webbrowser.open(config['source']['paragon_gideon']);webbrowser.open(config['source']['readme'])
    if args.source_content:install(args.source_content,args.with_course_effects,args.with_minions,args.with_course_animation)
    elif not args.open_sources:parser.error('Use --source-content or --open-sources')

if __name__=='__main__':main()
