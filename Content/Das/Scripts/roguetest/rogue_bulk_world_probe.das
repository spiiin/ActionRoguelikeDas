options gen2
module rogue_bulk_world_probe public
require ue_navigation public
require ue_vector_math public
require ue_instanced_mesh public

[ue_class(module_id="roguetest", Blueprintable)]
class RogueBulkWorldProbe : Actor {
    [ue_function(BlueprintCallable)]
    def Validate(origin : UEVector; mesh : InstancedStaticMeshComponentRef) : bool {
        var passed = false
        with_ue_navigation() $(navigation : NavigationSystemRef) {
            let point = ue_navigation_random_point(navigation, origin, 100.0f)
            verify(point.Found, "Native navigation point unavailable on prepared course map")
            let points <- ue_navigation_random_points(navigation, origin, 100.0f, 16)
            verify(length(points) == 16, "Navigation batch size mismatch")
            for (location in points) { verify(length(location-origin) <= 101.0lf, "Point outside query radius") }
            let fallback <- ue_navigation_random_points(default<NavigationSystemRef>, origin, 100.0f, 3)
            for (location in fallback) { verify(location == origin, "Missing navigation must fall back to origin") }
            let none <- ue_navigation_random_points(navigation, origin, 100.0f, 0)
            verify(empty(none), "Zero navigation count")
            var rejected = false
            try { let bad <- ue_navigation_random_points(navigation, origin, 100.0f, -1) } recover { rejected = true }
            verify(rejected, "Negative navigation count must fail")
            passed = true
        }
        var transforms <- [ue_transform(origin, UE_ROTATOR_ZERO, UE_VECTOR_ONE),
                           ue_transform(origin+UE_VECTOR_UP, UE_ROTATOR_ZERO, UE_VECTOR_ONE)]
        let ids <- ue_ism_add_instances(mesh, transforms)
        verify(length(ids) == 2 && ids[0] != ids[1], "Bulk ISM IDs")
        let retained = ue_ism_instance_index(mesh, ids[1])
        var first <- [ids[0]]
        verify(ue_ism_remove_instances(mesh, first), "Bulk ISM remove")
        verify(ue_ism_instance_index(mesh, ids[0]) == -1, "Removed ID remains valid")
        verify(ue_ism_instance_index(mesh, ids[1]) >= 0, "Other stable ID lost")
        var last <- [ids[1]]
        verify(ue_ism_remove_instances(mesh, last), "Final ISM remove")
        return passed
    }
}
