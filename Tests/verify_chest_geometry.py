import unreal,math
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
c=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_InteractiveChestHinged_C')
h=c.get_editor_property('LidMeshComponent')
v=c.get_editor_property('LidVisual')
b=c.get_editor_property('BaseMeshComponent')
space=unreal.RelativeTransformSpace.RTS_WORLD
body=b.get_socket_transform('None',space)
body_poly=[(-50,-50),(50,-50),(50,50),(-50,50)]
intersections=[]
try:
    for angle in range(121):
        h.set_relative_rotation(unreal.Rotator(pitch=angle,yaw=0,roll=0),False,True)
        pose=v.get_socket_transform('None',space)
        poly=[]
        for x,z in [(-50,-50),(50,-50),(50,50),(-50,50)]:
            world=unreal.MathLibrary.transform_location(pose,unreal.Vector(x,0,z))
            local=unreal.MathLibrary.inverse_transform_location(body,world)
            poly.append((local.x,local.z))
        axes=[(1,0),(0,1)]
        for i,p in enumerate(poly):
            q=poly[(i+1)%4]
            dx,dz=q[0]-p[0],q[1]-p[1]
            length=math.hypot(dx,dz)
            axes.append((-dz/length,dx/length))
        overlapping=True
        for ax,az in axes:
            a=[x*ax+z*az for x,z in poly]
            d=[x*ax+z*az for x,z in body_poly]
            if min(max(a),max(d))-max(min(a),min(d))<=0.001:
                overlapping=False
                break
        if overlapping: intersections.append(angle)
finally:
    h.set_relative_rotation(unreal.Rotator(0,0,0),False,True)
assert not intersections,intersections
print('GEOMETRY PASS: no interior overlap, 121 angles from 0 to 120 degrees')
c.call_method('Interact')
print('animation started',c.get_editor_property('LastDasError'))
