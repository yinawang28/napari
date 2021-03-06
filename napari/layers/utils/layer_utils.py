import numpy as np


def increment_unnamed_colormap(name, names):
    """Increment name for unnamed colormap.

    Parameters
    ----------
    name : str
        Name of colormap to be incremented.
    names : List[str]
        Names of existing colormaps.

    Returns
    -------
    name : str
        Name of colormap after incrementing.
    """
    if name == '[unnamed colormap]':
        past_names = [n for n in names if n.startswith('[unnamed colormap')]
        name = f'[unnamed colormap {len(past_names)}]'
    return name


def calc_data_range(data):
    """Calculate range of data values. If all values are equal return [0, 1].

    Parameters
    -------
    data : array
        Data to calculate range of values over.

    Returns
    -------
    values : list of float
        Range of values.

    Notes
    -----
    If the data type is uint8, no calculation is performed, and 0-255 is
    returned.
    """
    if data.dtype == np.uint8:
        return [0, 255]
    if np.prod(data.shape) > 1e6:
        # If data is very large take the average of the top, bottom, and
        # middle slices
        bottom_plane_idx = (0,) * (data.ndim - 2)
        middle_plane_idx = tuple(s // 2 for s in data.shape[:-2])
        top_plane_idx = tuple(s - 1 for s in data.shape[:-2])
        idxs = [bottom_plane_idx, middle_plane_idx, top_plane_idx]
        reduced_data = [
            [np.max(data[idx]) for idx in idxs],
            [np.min(data[idx]) for idx in idxs],
        ]
    else:
        reduced_data = data

    min_val = np.min(reduced_data)
    max_val = np.max(reduced_data)

    if min_val == max_val:
        min_val = 0
        max_val = 1
    return [float(min_val), float(max_val)]


def segment_normal(a, b, p=(0, 0, 1)):
    """Determines the unit normal of the vector from a to b.

    Parameters
    ----------
    a : np.ndarray
        Length 2 array of first point or Nx2 array of points
    b : np.ndarray
        Length 2 array of second point or Nx2 array of points
    p : 3-tuple, optional
        orthogonal vector for segment calculation in 3D.

    Returns
    -------
    unit_norm : np.ndarray
        Length the unit normal of the vector from a to b. If a == b,
        then returns [0, 0] or Nx2 array of vectors
    """
    d = b - a

    if d.ndim == 1:
        if len(d) == 2:
            normal = np.array([d[1], -d[0]])
        else:
            normal = np.cross(d, p)
        norm = np.linalg.norm(normal)
        if norm == 0:
            norm = 1
    else:
        if d.shape[1] == 2:
            normal = np.stack([d[:, 1], -d[:, 0]], axis=0).transpose(1, 0)
        else:
            normal = np.cross(d, p)

        norm = np.linalg.norm(normal, axis=1, keepdims=True)
        ind = norm == 0
        norm[ind] = 1
    unit_norm = normal / norm

    return unit_norm


def convert_to_uint8(data: np.ndarray) -> np.ndarray:
    """
    Convert array content to uint8.

    If all negative values are changed on 0.

    If values are integer and bellow 256 it is simple casting otherwise maximum value for this data type is picked
    and values are scaled by 255/maximum type value.

    Binary images ar converted to [0,255] images.

    float images are multiply by 255 and then casted to uint8.

    Based on skimage.util.dtype.convert but limited to output type uint8
    """
    out_dtype = np.dtype(np.uint8)
    out_max = np.iinfo(out_dtype).max
    if data.dtype == out_dtype:
        return data
    in_kind = data.dtype.kind
    if in_kind == "b":
        return data.astype(out_dtype) * 255
    if in_kind == "f":
        image_out = np.multiply(data, out_max, dtype=data.dtype)
        np.rint(image_out, out=image_out)
        np.clip(image_out, 0, out_max, out=image_out)
        return image_out.astype(out_dtype)

    if in_kind in "ui":
        if in_kind == "u":
            if data.max() < out_max:
                return data.astype(out_dtype)
            return np.right_shift(data, (data.dtype.itemsize - 1) * 8).astype(
                out_dtype
            )
        else:
            np.maximum(data, 0, out=data, dtype=data.dtype)
            if data.dtype == np.int8:
                return (data * 2).astype(np.uint8)
            if data.max() < out_max:
                return data.astype(out_dtype)
            return np.right_shift(
                data, (data.dtype.itemsize - 1) * 8 - 1
            ).astype(out_dtype)
