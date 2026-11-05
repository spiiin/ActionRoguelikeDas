"""Read-only export of the course map, including all world-partition actors."""
from pathlib import Path
from collections import Counter
import unreal,json,traceback,hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Saved/Tests/original_world';OUT.mkdir(parents=True,exist_ok=True)

def vec(v):return [v.x,v.y,v.z]
def rot(v):return [v.pitch,v.yaw,v.roll]
def pose(actor):return dict(location=vec(actor.get_actor_location()),rotation=rot(actor.get_actor_rotation()),scale=vec(actor.get_actor_scale3d()))
def graph_data(bp):
    lib=unreal.BlueprintEditorLibrary;pins=unreal.BlueprintGraphPinLibrary
    graphs={g.get_path_name() for g in lib.list_graphs(bp)};nodes=[]
    for node in unreal.ObjectIterator(unreal.load_class(None,'/Script/BlueprintGraph.K2Node')):
        if node.get_outer().get_path_name() not in graphs:continue
        nodes.append(dict(name=node.get_name(),title=lib.get_node_title(node),kind=node.get_class().get_name(),pins=[dict(name=str(pins.get_pin_name(p)),value=pins.get_pin_value(p),links=[(pins.get_owning_node(o).get_name(),str(pins.get_pin_name(o))) for o in pins.list_connected_pins(p)]) for p in lib.list_all_pins(node)]))
    return nodes
STATE={'ticks':0}
def export_world():
    try:
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        assert world.get_name()=='P_OpenWorldTestMap',world
        descs=STATE['descs']
        actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        all_actors=list(actors.get_all_level_actors());items=[]
        game_classes={};native=[]
        for actor in all_actors:
            cls=actor.get_class();path=cls.get_path_name()
            item=dict(name=actor.get_name(),label=actor.get_actor_label(),kind=path,pose=pose(actor),components=[],properties={})
            keys=['HealingAmount','PickupSound','SpawnInterval','AnimationSpeed','AnimationTargetPitch','RespawnDelay','CreditsToDrop','InitialCoinCount','SpawnRadius','Directors','GlobalStartingSeed','OnHandlePulled','primary_actor_tick','default_pawn_class']
            bp=None
            if path.startswith('/Game/'):
                bp=unreal.load_asset(path[:-2])
                if bp:
                    keys+=list(map(str,unreal.BlueprintEditorLibrary.list_member_variable_names(bp)))
                    if path not in game_classes:game_classes[path]=dict(nodes=graph_data(bp))
            for key in set(keys):
                try:
                    v=actor.get_editor_property(key);item['properties'][key]=v.get_path_name() if isinstance(v,unreal.Object) else str(v)
                except Exception:pass
            for c in [v for v in unreal.ObjectIterator(unreal.SceneComponent) if v.get_outer()==actor]:
                cp=dict(name=c.get_name(),kind=c.get_class().get_path_name(),location=vec(c.get_editor_property('relative_location')),rotation=rot(c.get_editor_property('relative_rotation')),scale=vec(c.get_editor_property('relative_scale3d')))
                parent=c.get_attach_parent();cp['parent']=parent.get_name() if parent else None
                cp['world_location']=vec(c.get_world_location());cp['world_rotation']=rot(c.get_world_rotation());cp['world_scale']=vec(c.get_world_scale())
                for field in ['asset','sound']:
                    try:
                        value=c.get_editor_property(field)
                        if isinstance(value,unreal.Object):cp[field]=value.get_path_name()
                    except Exception:pass
                for field in ['box_extent','sphere_radius','capsule_half_height','capsule_radius']:
                    try:
                        value=c.get_editor_property(field);cp[field]=vec(value) if isinstance(value,unreal.Vector) else value
                    except Exception:pass
                if isinstance(c,unreal.StaticMeshComponent):
                    m=c.get_editor_property('static_mesh');cp['mesh']=m.get_path_name() if m else None
                    cp['materials']=[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())]
                    cp['collision']=str(c.get_collision_profile_name())
                item['components'].append(cp)
            task=unreal.AssetExportTask();task.object=actor;task.filename=str(OUT/(actor.get_name()+'.t3d'));task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=unreal.ObjectExporterT3D()
            unreal.Exporter.run_asset_export_task(task)
            items.append(item)
            if path.startswith('/Script/') and not path.startswith('/Script/ActionRoguelike.') and cls.get_name() not in ['WorldSettings','LevelScriptActor','WorldPartitionMiniMap','WorldDataLayers','WorldPartitionHLOD']:
                native.append(actor)
        level=next(a for a in all_actors if isinstance(a,unreal.PlayerStart)).get_level()
        (OUT/'actors.json').write_text(json.dumps(items,indent=2))
        level_graphs={}
        for obj in unreal.ObjectIterator(unreal.LevelScriptBlueprint):
            if 'P_OpenWorldTestMap' in obj.get_path_name():
                level_graphs['path']=obj.get_path_name();level_graphs['nodes']=graph_data(obj)
        for key in ['level_script_blueprint','level_script_actor']:
            try:
                obj=level.get_editor_property(key)
                level_graphs[key]=obj.get_path_name() if obj else None
                if isinstance(obj,unreal.Blueprint):
                    level_graphs['nodes']=graph_data(obj)
                    task=unreal.AssetExportTask();task.object=obj;task.filename=str(OUT/'level_blueprint.t3d');task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=unreal.ObjectExporterT3D()
                    unreal.Exporter.run_asset_export_task(task)
            except Exception as e:level_graphs[key]=str(e)
        actors.set_selected_level_actors(native)
        task=unreal.AssetExportTask();task.object=world;task.filename=str(OUT/'native_geometry.t3d');task.automated=True;task.prompt=False;task.replace_identical=True;task.selected=True;task.exporter=unreal.LevelExporterT3D()
        geometry=unreal.Exporter.run_asset_export_task(task)
        settings=next(a for a in unreal.ObjectIterator(unreal.WorldSettings) if a.get_outer()==level)
        mode=settings.get_editor_property('default_game_mode') or unreal.load_class(None,'/Game/ActionRoguelike/BP_GameMode.BP_GameMode_C')
        mode_data={}
        director_data=[]
        if mode:
            cdo=unreal.get_default_object(mode)
            task=unreal.AssetExportTask();task.object=cdo;task.filename=str(OUT/'game_mode.t3d');task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=unreal.ObjectExporterT3D()
            unreal.Exporter.run_asset_export_task(task)
            for value in cdo.get_editor_property('Directors'):
                entry={}
                for key in ['SpawnLocationQuery','MonsterSpawnTable','TickInterval','TimeBetweenWaves','DebugDisplayName','CreditGainCurve']:
                    try:
                        v=value.get_editor_property(key)
                        entry[key]=v.get_path_name() if isinstance(v,unreal.Object) else str(v)
                        if key=='CreditGainCurve':
                            entry['curve_text']=v.export_text()
                            curve=v.get_editor_property('EditorCurveData')
                            entry['curve_keys']=[dict(time=k.get_editor_property('time'),value=k.get_editor_property('value'),interp=str(k.get_editor_property('interp_mode')),arrive=k.get_editor_property('arrive_tangent'),leave=k.get_editor_property('leave_tangent')) for k in curve.get_editor_property('Keys')]
                        if key=='MonsterSpawnTable' and v:
                            entry['rows']=json.loads(unreal.DataTableFunctionLibrary.export_data_table_to_json_string(v))
                    except Exception as e:entry[key+'_error']=str(e)
                director_data.append(entry)
            for key in ['Directors','GlobalStartingSeed','default_pawn_class','player_controller_class']:
                try:
                    v=cdo.get_editor_property(key);mode_data[key]=v.get_path_name() if isinstance(v,unreal.Object) else str(v)
                except Exception:pass
        if director_data:
            query=unreal.load_asset(director_data[0]['SpawnLocationQuery'])
            task=unreal.AssetExportTask();task.object=query;task.filename=str(OUT/'spawn_query.t3d');task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=unreal.ObjectExporterT3D()
            unreal.Exporter.run_asset_export_task(task)
            for entry in director_data:
                for row in entry.get('rows',[]):
                    profile=unreal.load_asset(row['MonsterData'])
                    if profile:
                        row['LootCoins']=profile.get_editor_property('LootCoins')
                        row['Actions']=[v.get_path_name() for v in profile.get_editor_property('Actions')]
        payload=dict(passed=True,source='/Game/ActionRoguelike/Maps/P_OpenWorldTestMap',descriptors=len(descs),actors=items,classes=dict(Counter(a['kind'] for a in items)),blueprints=game_classes,level=level_graphs,geometry=geometry,game_mode=mode.get_path_name() if mode else None,game_mode_defaults=mode_data,directors=director_data)
    except Exception:payload=dict(passed=False,error=traceback.format_exc())
    (OUT/'reference.json').write_text(json.dumps(payload,indent=2))
    print('DAS_ORIGINAL_WORLD_REFERENCE='+str(payload['passed']))
    unreal.SystemLibrary.quit_editor()

def tick(delta):
    STATE['ticks']+=1
    if STATE['ticks']==1:
        descs=unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
        if isinstance(descs,tuple):descs=next(x for x in descs if isinstance(x,(list,unreal.Array)))
        STATE['descs']=descs
        unreal.WorldPartitionBlueprintLibrary.load_actors([d.get_editor_property('guid') for d in descs])
    if STATE['ticks']>=4:
        unreal.unregister_slate_post_tick_callback(STATE['handle'])
        export_world()
STATE['handle']=unreal.register_slate_post_tick_callback(tick)
