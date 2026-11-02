"""Fetch the pinned author's course resources for local use, then install them.

No resource files are served by this repository. The source's licensing terms
apply independently; fetching assets does not grant a license or change them.
For Epic account acquisition, use setup_external_assets.py --open-sources.
"""
import argparse
import json
import subprocess
from pathlib import Path
from setup_external_assets import ROOT, MANIFEST, install

def git(cache,*args):
    subprocess.run(['git','-C',str(cache),*args],check=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=ROOT/'Saved/ExternalAssets/Source')
    parser.add_argument('--with-course-effects',action='store_true')
    args=parser.parse_args()
    config=json.loads(MANIFEST.read_text())
    source=config['source'];cache=args.cache.resolve()
    print('Publisher/source terms:',source['readme'])
    if not (cache/'.git').is_dir():
        cache.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['git','clone','--filter=blob:none','--sparse','--no-checkout','--depth=1',
            '--branch',source['branch'],source['repository'],str(cache)],check=True)
    remote=subprocess.check_output(['git','-C',str(cache),'remote','get-url','origin'],text=True).strip()
    if remote!=source['repository']:raise RuntimeError('Cache belongs to a different source repository')
    present=subprocess.run(['git','-C',str(cache),'cat-file','-e',source['revision']+'^{commit}'],capture_output=True)
    if present.returncode:git(cache,'fetch','--depth=1','origin',source['revision'])
    git(cache,'sparse-checkout','set',*config['download_folders'])
    git(cache,'checkout','--detach',source['revision'])
    install(cache/'Content',args.with_course_effects)

if __name__=='__main__':main()
