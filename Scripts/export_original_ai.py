"""Read-only export of the pinned course AI assets. Run in the original editor."""
import hashlib,json,traceback
from pathlib import Path
import unreal
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Saved/Tests/original_ai'
OUT.mkdir(parents=True,exist_ok=True)
receipt=ROOT/'Saved/Tests/original_ai_reference.json'
try:
    files={}
    for name in ['MinionRangedBT','MinionRangedBB','EQS_TargetSelection','EQS_MoveToTarget','EQS_MoveToCover']:
        asset=unreal.load_asset('/Game/ActionRoguelike/AI/'+name)
        assert asset,name
        filename=OUT/(name+'.t3d')
        task=unreal.AssetExportTask()
        task.object=asset;task.filename=str(filename)
        task.automated=True;task.prompt=False;task.replace_identical=True
        task.exporter=unreal.ObjectExporterT3D()
        assert unreal.Exporter.run_asset_export_task(task),name
        files[name]={'text':str(filename),'sha256':hashlib.sha256(filename.read_bytes()).hexdigest()}
    payload={'passed':True,'project':unreal.Paths.project_dir(),'files':files}
except Exception:
    payload={'passed':False,'error':traceback.format_exc()}
receipt.write_text(json.dumps(payload,indent=2),encoding='utf-8')
print('DAS_ORIGINAL_AI_REFERENCE='+str(payload['passed']))
unreal.SystemLibrary.quit_editor()
