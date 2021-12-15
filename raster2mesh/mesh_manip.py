import time

import numpy as np
import open3d as o3d


# from pointcloud to mesh
# TODO check if output mesh needs optimization to be watertight
# https://towardsdatascience.com/5-step-guide-to-generate-3d-meshes-from-point-clouds-with-python-36bad397d8ba
def pcd2mesh(surface_pcd, mesh_out, resolution, method="Poisson"):
    start = time.time()

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(surface_pcd[:, :3])
    pcd.estimate_normals()

    print(f"- Computing mesh using {method} method...")
    if method == "Poisson":
        # mesh resolution can be defined "directly" by cell edge width or by depth of octree.
        # Here we opt for the second option, however width can only be int.
        # poisson_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=8, width=0, scale=1.1, linear_fit=False)[0]
        poisson_mesh = \
        o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, width=resolution, scale=1.1, linear_fit=False)[0]
        bbox = pcd.get_axis_aligned_bounding_box()

        p_mesh_crop = poisson_mesh.crop(bbox)

        o3d.io.write_triangle_mesh(mesh_out, p_mesh_crop)

    elif method == "BPA":  # very slow for large meshes + not multi-threaded
        distances = pcd.compute_nearest_neighbor_distance()
        avg_dist = np.mean(distances)
        radius = 3 * avg_dist

        bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd, o3d.utility.DoubleVector(
            [radius, radius * 2]))
        dec_mesh = bpa_mesh.simplify_quadric_decimation(100000)

        dec_mesh.remove_degenerate_triangles()
        dec_mesh.remove_duplicated_triangles()
        dec_mesh.remove_duplicated_vertices()
        dec_mesh.remove_non_manifold_edges()

        o3d.io.write_triangle_mesh(mesh_out, dec_mesh)

    else:
        print("* Unknown mesh-ify method, options are 'Poisson' or 'BPA'. Exit.")
        exit(1)

    end = time.time()
    print(f"- Mesh written to {mesh_out} after {int(end - start)} seconds.")


# cut mesh based on bounding box
def cut_mesh(mesh_in, mesh_out, bbox=None, bounds=[]):
    import meshio
    from matplotlib.path import Path

    # check out input bounding box
    if bbox != None:
        print("# Sometimes y and x are messed up, safer to pass [xmin, xmax, ymin, ymax] directly.")
        xx0, yy0, xx1, yy1 = bbox.bounds
    elif len(bounds) == 4:
        xx0, xx1, yy0, yy1 = bounds
    else:
        print("* cut_mesh needs either a Shapely.box or bounds=[xmin,xmax,ymin,ymax]. Exit.")
        exit(1)

    # import input mesh
    mesh = meshio.read(filename=mesh_in)
    V = mesh.points
    F = mesh.cells[0].data

    # use rectangle.contains_points on V to select only points falling within
    rectangle_selection = np.array([[xx0, yy0], [xx1, yy0], [xx1, yy1], [xx0, yy1]])
    p = Path(rectangle_selection)
    mask = p.contains_points(V[:, :2])

    # mask is used to select only cells F where all vertices V are inside rectangle
    mask_dict = dict(enumerate(mask.flatten()))
    u, inv = np.unique(F, return_inverse=True)
    F_new = F[np.all(np.array([mask_dict[x] for x in u])[inv].reshape(F.shape), axis=1)]

    # write to mesh_out
    mesh = meshio.Mesh(V, [('triangle', F_new)])
    mesh.write(mesh_out)

    print(f"- {mesh_in} cropped and written to {mesh_out}.")
