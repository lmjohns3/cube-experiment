import contextlib
import lmj.plot
import numpy as np


@contextlib.contextmanager
def space(show_afterwards=True):
    '''Produce a 3D plotting axes, for use in a with statement.'''
    fig = lmj.plot.figure(figsize=(11, 4))
    ax = lmj.plot.create_axes(111, projection='3d', aspect='equal', spines=None)
    yield ax
    ax.set_xlim([-2, 2])
    ax.set_ylim([-2, 2])
    ax.set_zlim([ 0, 2])
    ax.set_xticks([-2, -1, 0, 1, 2])
    ax.set_yticks([-2, -1, 0, 1, 2])
    ax.set_zticks([0, 1, 2])
    ax.w_xaxis.set_pane_color((1, 1, 1, 1))
    ax.w_yaxis.set_pane_color((1, 1, 1, 1))
    ax.w_zaxis.set_pane_color((1, 1, 1, 1))
    if show_afterwards:
        lmj.plot.show()


def show_cubes(ax, trial, target_num=None):
    '''Plot markers for target cubes on the given axes.

    Parameters
    ----------
    ax : plotting axes
    trial : Trial object
    target_num : int or set of int, optional
        If given, only show this/these targets.
    '''
    if target_num is None:
        target_num = range(12)
    elif isinstance(target_num, int):
        target_num = (target_num, )
    to_plot = set(target_num)
    xs, ys, zs = [-1000], [-1000], [-1000]
    for flavor in ('source', 'target'):
        cols = [flavor + suffix for suffix in ('', '-x', '-y', '-z')]
        for _, (n, x, y, z) in trial.df[cols].drop_duplicates().iterrows():
            if n in to_plot:
                to_plot.remove(n)
                xs.append(x)
                ys.append(y)
                zs.append(z)
                ax.text(x, z - 0.1, y + 0.1, str(int(n)))
    ax.scatter(xs, zs, ys, marker='o', s=200, color='#111111', linewidth=0, alpha=0.7)


SKELETON_SEGMENTS = (
    # legs
    ['l-ilium', 'l-knee', 'l-shin', 'l-ankle', 'l-heel', 'l-mt-outer', 'l-mt-inner'],
    ['r-ilium', 'r-knee', 'r-shin', 'r-ankle', 'r-heel', 'r-mt-outer', 'r-mt-inner'],
    # arms
    ['t3', 'r-collar', 'r-shoulder', 'r-elbow', 'r-wrist', 'r-mc-inner', 'r-fing-index'],
    ['t3', 'l-collar', 'l-shoulder', 'l-elbow', 'l-wrist', 'l-mc-inner', 'l-fing-index'],
    # head + torso
    ['r-head-front', 'l-head-back', 'l-head-front', 'r-head-back',
     't3', 't9', 'l-ilium', 'r-ilium', 'r-hip', 'l-hip', 'abdomen', 'sternum'],
)

def skeleton(ax, trial, frame, show_labels=(), **kwargs):
    '''Plot a skeleton based on a frame of the given trial.

    Parameters
    ----------
    ax : Axes
    trial : Movement
    frame : int or float
    show_labels : sequence of string
    '''
    idx = trial.df.index[frame]
    fr = lambda m: trial.trajectory(m, velocity=True).loc[idx, :]
    frames = {m[9:]: fr(m) for m in trial.marker_columns}

    # plot marker positions.
    sckwargs = dict(kwargs)
    for k in ('lw', 'linewidth'):
        if k in sckwargs:
            sckwargs.pop(k)
    ax.scatter([f.x for f in frames.values()],
               [f.z for f in frames.values()],
               zs=[f.y for f in frames.values()],
               s=40, lw=0, color='#d62728', **sckwargs)

    # plot marker velocities.
    dt = 0.2
    for f in frames.values():
        ax.plot([f.x, f.x + dt * f.vx],
                [f.z, f.z + dt * f.vz],
                zs=[f.y, f.y + dt * f.vy],
                alpha=0.4, color='#17becf')

    # plot skeleton segments.
    for segment in SKELETON_SEGMENTS:
        xs, ys, zs = [], [], []
        for m in segment:
            xs.append(frames[m].x)
            ys.append(frames[m].y)
            zs.append(frames[m].z)
        ax.plot(xs, zs, zs=ys, alpha=0.5, color='#111111', **kwargs)

    # plot marker labels.
    for m, f in frames.items():
        if m in show_labels:
            ax.text(f.x, f.z + 0.05, f.y + 0.05, str(m))


u, v = np.mgrid[0:2 * np.pi:17j, 0:np.pi:13j]
sphere = np.array([np.cos(u) * np.sin(v), np.sin(u) * np.sin(v), np.cos(v)])

def ellipsoid(center, radius):
    '''Return a grid of points defining an ellipsoid at the given location.

    At the moment this function returns an axis-aligned ellipsoid.

    Parameters
    ----------
    center : array (3, )
        The center of the ellipsoid.
    radius : array (3, )
        The radius of the ellipsoid along each of the coordinate axes.

    Returns
    -------
    array (3, lat, long) :
        An array of points on the surface of an axis-aligned ellipsoid.
    '''
    return (center + sphere.T * radius).T
