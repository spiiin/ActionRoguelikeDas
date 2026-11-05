"""Preserve the exported, already merged terrain when importing a course scene.

UE's PostLoad-only edit-layer flag is unset for text-imported proxies. Their
first registration otherwise copies final data over the source base layer and
then adds the other layers again. Import final data as a single native layer;
keep the complete editable source exports outside the generated import file.
"""
import re


def bake_landscape_actor(text):
    final_names=set(re.findall(r'HeightmapTexture=.*?\.(Heightmap_\d+)\x27',text))
    layer_names=set()
    for line in text.splitlines():
        if line.lstrip().startswith('LayersData='):
            layer_names.update(re.findall(r'\.(Heightmap_\d+)\x27',line))
    removed=layer_names-final_names
    removed.update(re.findall(r'Begin Object Class=/Script/Landscape\.LandscapeEditLayer[^\n]*Name="([^"]+)"',text))
    result=[]
    skipping=0
    for line in text.splitlines(keepends=True):
        begin=re.match(r'\s*Begin Object\b.*?Name="([^"]+)"',line)
        if skipping:
            if begin:skipping+=1
            elif line.strip()=='End Object':skipping-=1
            continue
        if begin and begin[1] in removed:
            skipping=1
            continue
        if line.lstrip().startswith(('LayersData=','LandscapeEditLayers(','LandscapeEditLayers=')):
            continue
        result.append(line)
    assert not skipping,'Unbalanced exported object block'
    baked=''.join(result)
    assert set(re.findall(r'HeightmapTexture=.*?\.(Heightmap_\d+)\x27',baked))==final_names
    return baked


def bake_landscape_scene(text):
    def actor(match):
        block=match[0]
        return bake_landscape_actor(block) if '/Script/Landscape.' in block.splitlines()[0] else block
    return re.sub(r'^[ \t]*Begin Actor\b.*?^[ \t]*End Actor[ \t]*(?:\n|$)',actor,text,flags=re.M|re.S)


def surface_samples(actor_text, components):
    """One original height sample per component, independent of actor poses alone."""
    stack=[]
    textures={}
    formats={}
    bindings={}
    for line in actor_text.splitlines():
        begin=re.match(r'\s*Begin Object\b.*?Name="([^"]+)"',line)
        if begin:stack.append(begin[1])
        if line.strip()=='End Object' and stack:stack.pop()
        if line.lstrip().startswith('Source=('):
            formats[stack[-1]]=line
        if 'CustomProperties TextureSourceData PayloadSize=' in line:
            fields=line.split('PayloadSize=',1)[1].split()
            textures[stack[-1]]=bytes(int(value,16) for value in fields[1:])
        if 'HeightmapTexture=' in line:
            binding=re.search(r'\.(Heightmap_\d+)\x27',line)
            assert binding,line
            bindings[stack[-1]]=binding[1]
    samples=[]
    for component in components:
        texture=bindings.get(component['name'])
        if not texture:continue
        # 128x128 packed BGRA textures; quad 32 is on the full-resolution
        # collision grid and before the duplicated subsection edge at 63.
        raw=textures[texture]
        assert 'SizeX=128,SizeY=128' in formats[texture]
        assert 'CompressionFormat=TSCF_UEDELTA' in formats[texture]
        assert 'Format=TSF_BGRA8' in formats[texture]
        assert len(raw)>=128*128*4
        # TextureSourceData carries UEDELTA, not decoded pixels. For a 128x128
        # BGRA8 mip the codec stores row zero then byte deltas to the prior row
        # (ImageCoreDelta.cpp; one tile, zero bias for 8-bit channels).
        red=sum(raw[(y*128+32)*4+2] for y in range(33)) & 255
        green=sum(raw[(y*128+32)*4+1] for y in range(33)) & 255
        height=(red<<8)|green
        location=component['world_location'];scale=component['world_scale']
        assert all(abs(angle)<.0001 for angle in component['world_rotation'])
        samples.append(dict(component=component['name'],
            x=location[0]+32*scale[0],y=location[1]+32*scale[1],
            z=location[2]+(height-32768)*scale[2]/128))
    assert len(samples)==4,len(samples)
    return samples
