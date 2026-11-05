"""Read-only inspection of the pinned course environment Blueprints."""
import unreal,json,traceback,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Saved/Tests/original_environment'
OUT.mkdir(parents=True,exist_ok=True)
try:
    result={}
    lib=unreal.BlueprintEditorLibrary;pins=unreal.BlueprintGraphPinLibrary
    for name in ['BP_Lever','BP_ProjectileSpammer']:
        path='/Game/ActionRoguelike/World/'+name
        bp=unreal.load_asset(path);assert bp and bp.generated_class(),name
        obj=unreal.get_default_object(bp.generated_class())
        values={}
        for key in lib.list_member_variable_names(bp):
            try:
                v=obj.get_editor_property(str(key));values[str(key)]=v.get_path_name() if isinstance(v,unreal.Object) else str(v)
            except Exception:pass
        graphs={g.get_path_name() for g in lib.list_graphs(bp)};nodes=[]
        for node in unreal.ObjectIterator(unreal.load_class(None,'/Script/BlueprintGraph.K2Node')):
            if node.get_outer().get_path_name() not in graphs:continue
            info=dict(name=node.get_name(),type=node.get_class().get_name(),title=lib.get_node_title(node),pins=[])
            for pin in lib.list_all_pins(node):
                info['pins'].append(dict(name=str(pins.get_pin_name(pin)),value=pins.get_pin_value(pin),links=[(pins.get_owning_node(o).get_name(),str(pins.get_pin_name(o))) for o in pins.list_connected_pins(pin)]))
            nodes.append(info)
        task=unreal.AssetExportTask();task.object=bp;task.filename=str(OUT/(name+'.t3d'));task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=unreal.ObjectExporterT3D()
        unreal.Exporter.run_asset_export_task(task)
        tick=obj.get_editor_property('primary_actor_tick')
        ticking={k:str(tick.get_editor_property(k)) for k in ['tick_interval','start_with_tick_enabled']}
        components=[]
        prefix=bp.generated_class().get_path_name()+':'
        for component in unreal.ObjectIterator(unreal.ActorComponent):
            if not component.get_path_name().startswith(prefix):continue
            properties={}
            for key in ['relative_location','relative_rotation','relative_scale3d','static_mesh','mobility','collision_profile_name']:
                try:
                    v=component.get_editor_property(key);properties[key]=v.get_path_name() if isinstance(v,unreal.Object) else str(v)
                except Exception:pass
            components.append(dict(name=component.get_name(),kind=component.get_class().get_name(),properties=properties))
        result[name]=dict(defaults=values,nodes=nodes,ticking=ticking,components=components)
    payload=dict(passed=True,blueprints=result)
except Exception:payload=dict(passed=False,error=traceback.format_exc())
(OUT/'reference.json').write_text(json.dumps(payload,indent=2))
print('DAS_ORIGINAL_ENVIRONMENT_REFERENCE='+str(payload['passed']))
unreal.SystemLibrary.quit_editor()
