from pathlib import Path
import unreal,runpy,time,json
root=Path(__file__).resolve().parents[1]
context=runpy.run_path(str(root/'Tests/verify_course_world_pie.py'))
g=context['tick'].__globals__
original_finish=g['finish']
def finish_original(error=None):
    original_finish(error)
    (root/'Saved/Tests/rogue_coin_profile_pie.json').write_bytes((root/'Saved/Tests/rogue_course_world_pie.json').read_bytes())
def finish_profile(error=None):
    if error:return finish_original(error)
    try:
        coins=g['coins'];source=g['by_label']['RogueCoinTestActor'];w=g['world']
        coins.set_editor_property('AutoCollect',False)
        probe_class=unreal.load_class(None,'/Game/DasRogue/Tests/BP_RogueBulkWorldProbe.BP_RogueBulkWorldProbe_C')
        probe=unreal.GameplayStatics.get_actor_of_class(w,probe_class)
        assert probe,'Bulk probe missing in PIE'
        assert probe.call_method('Validate',args=(unreal.Vector(620,570,12),coins.get_editor_property('WorldISM')))
        g['s']['checks'].append('scoped_and_bulk_navigation_and_stable_ism_ids')
        probe.destroy_actor()
        output=[]
        for count in [100,1000,1000]:
            start=time.perf_counter();ok=source.call_method('SpawnCoins',args=(count,));elapsed=(time.perf_counter()-start)*1000
            assert ok
            output.append(dict(stage='das_spawn',count=count,ms=elapsed))
        locations=[unreal.Vector(620,570,12)]*1000
        start=time.perf_counter();assert coins.call_method('AddCoinPickups',args=(locations,[10]*1000))
        output.append(dict(stage='das_add_only',count=1000,ms=(time.perf_counter()-start)*1000))
        component=unreal.DasWorldComponentLibrary.create_native_world_component(w,'/Script/Engine.InstancedStaticMeshComponent','NativeISMProfile')
        component.set_static_mesh(coins.get_editor_property('CoinMesh'))
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        assert unreal.DasWorldComponentLibrary.register_world_component(w,component)
        transform=coins.get_editor_property('WorldISM').get_instance_transform(0,True)
        for count in [100,1000,1000]:
            data=[transform]*count
            start=time.perf_counter();ids=unreal.DasWorldComponentLibrary.add_instances_by_id(component,data,True,False)
            output.append(dict(stage='native_ism',count=count,ms=(time.perf_counter()-start)*1000))
            assert len(ids)==count
        unreal.DasWorldComponentLibrary.destroy_world_component(component)
        (root/'Saved/Tests/course_coin_profile.json').write_text(json.dumps(output,indent=2))
        print('COIN_PYTHON_PROFILE',output)
        finish_original()
    except Exception:
        import traceback
        finish_original(traceback.format_exc())
g['finish']=finish_profile
