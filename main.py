import pyvista as pv

from raster2mesh.mesh_manip import pcd2mesh, cut_mesh
from raster2mesh.raster_roi import roi2pcd, roi2box

if __name__ == '__main__':

    # select raster file to mesh-ify and output path
    raster_path = "data/LDEM_NP_300M_small.tif"
    mesh_path = "mesh.ply"

    # open raster and select region to mesh-ify
    # generate mesh of selected region
    pcd = roi2pcd(raster_in=raster_path, raster_out="cut.tif")
    pcd2mesh(pcd, mesh_out=mesh_path, resolution=1)

    # read and visualize resulting mesh
    grid = pv.read(mesh_path)
    grid.plot(show_scalar_bar=True, show_axes=False)

    # in case the mesh needs to be re-cropped...
    # select subregion (on same cropped raster) to re-crop mesh
    bbox = roi2box("cut.tif")
    # clip mesh for subregion
    cut_mesh(mesh_in=mesh_path, bounds=bbox, mesh_out='mesh_cut.ply')

    # read and visualize resulting mesh
    grid = pv.read('mesh_cut.ply')
    grid.plot(show_scalar_bar=True, show_axes=False)