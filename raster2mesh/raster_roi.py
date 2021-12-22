import time

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr


# Simple mouse click function to store coordinates
def on_click(event):
    ix, iy = event.xdata, event.ydata
    # print(ix, iy)

    # assign global variable to access outside of function
    coords.append((ix, iy))

    # Disconnect after 2 clicks
    if len(coords) == 4:
        plt.disconnect(binding_id)
        plt.close(1)
    return


# plot xarray/rio dataset and select region of interest, return coordinates
def select_roi(xr_dataset, resample=1.0):
    from rasterio.enums import Resampling
    global binding_id, coords

    # get 2d data (z) name for this raster
    data_name = list(xr_dataset.data_vars.keys())[0]

    # downsample to select roi w/o slowing things down
    upscale_factor = resample
    new_width = int(xr_dataset.rio.width * upscale_factor)
    new_height = int(xr_dataset.rio.height * upscale_factor)

    ds_downsampled = xr_dataset.rio.reproject(
        xr_dataset.rio.crs,
        shape=(new_height, new_width),
        resampling=Resampling.bilinear,
    )

    # plot downsampled raster with mouse binding to capture coordinates
    ds_downsampled[data_name].plot()
    coords = []
    binding_id = plt.connect('button_press_event', on_click)
    plt.title("Click 4 times to select the vertices of the ROI quadrangle.")
    plt.tight_layout()
    plt.show()

    return np.array(coords)


# generate point cloud of selected region
def roi2pcd(raster_in, raster_out=None):
    start = time.time()

    print(f"- Reading raster.")
    # open raster with xarray/rioxarray (only engine="rasterio" also reads crs)
    ds = xr.open_dataset(raster_in, engine="rasterio")

    # get 2d data (z) name for this raster
    data_name = list(ds.data_vars.keys())[0]

    # selected coordinates are used to clip initial raster (we need a box, but clip_box gives issues - workaround)
    coords = select_roi(ds, resample=0.1)
    xmin, xmax, ymin, ymax = np.min(coords[:, 0]), np.max(coords[:, 0]), np.min(coords[:, 1]), np.max(coords[:, 1])
    geometries = [
        {
            'type': 'Polygon',
            'coordinates': [[
                [xmin, ymax], [xmax, ymax], [xmax, ymin], [xmin, ymin]
            ]]
        }
    ]
    # clip_box gives a weird error (see https://github.com/corteva/rioxarray/issues/286 ),
    # we still need/make a quadrangular box
    # ds_clip = ds.rio.clip_box(np.min(coords[:, 0]), np.max(coords[:, 0]), np.min(coords[:, 1]), np.max(coords[:, 1]))
    ds_clip = ds.rio.clip(geometries)

    if raster_out != None:
        ds_clip.squeeze().rio.to_raster(raster_out)

    # show clipped region for debug
    # ds_clip[data_name].plot()
    # plt.show()

    # generate xyz pointcloud as numpy array
    xv, yv = np.meshgrid(ds_clip.x.values, ds_clip.y.values)
    zv = ds_clip[data_name].values
    surface_pcd = np.row_stack([xv.ravel(), yv.ravel(), zv.ravel()]).T

    end = time.time()
    print(f"- Point cloud of the selected region generated after {int(end - start)} seconds.")

    return surface_pcd


# generate (xmin, xmax, ymin, ymax) of region selected on raster
def roi2box(raster_in):
    # from shapely.geometry import box

    start = time.time()

    print(f"- Reading raster.")
    # open raster with xarray/rioxarray (only engine="rasterio" also reads crs)
    ds = xr.open_dataset(raster_in, engine="rasterio")

    # select region of interest and produce box
    roi_coords = select_roi(ds, resample=0.1)
    # bbox = box(np.min(roi_coords[:, 0]), np.max(roi_coords[:, 0]), np.min(roi_coords[:, 1]), np.max(roi_coords[:, 1])) # sometimes this messes up coords
    xmin, xmax, ymin, ymax = np.min(roi_coords[:, 0]), np.max(roi_coords[:, 0]), np.min(roi_coords[:, 1]), np.max(roi_coords[:, 1])

    end = time.time()
    print(f"- Bounding box [xmin, xmax, ymin, ymax] of the selected region generated after {int(end - start)} seconds.")

    return xmin, xmax, ymin, ymax
