#!/usr/bin/env python

import climate
import itertools
import lmj.cubes
import lmj.plot
import numpy as np
import pandas as pd

FRAME_RATE = 100
MARKERS = 'r-fing-index l-fing-index r-heel   r-head-front'
_COLORS = '#111111      #d62728      #1f77b4  #2ca02c'
COLORS = dict(zip(MARKERS.split(), _COLORS.split()))

@climate.annotate(
    root='read subject data from this file tree',
    pattern=('plot data from files matching this pattern', 'option'),
    output=('save movie in this output filename', 'option'),
    target=('plot data for this target', 'option', None, int),
    approach_sec=('plot variance for N sec prior to target acquisition', 'option', None, float),
)
def main(root, pattern='*/*/*trial00*', output=None, target=3, approach_sec=1):
    targets = None
    num_frames = int(FRAME_RATE * approach_sec)

    # first, read trial data and extract marker trajectories. group by marker
    # and source cube.
    data = {}
    for trial in lmj.cubes.Experiment(root).trials_matching(pattern):
        trial.load()
        targets = trial
        move = trial.movement_to(target)
        move.df.index = pd.Index(np.arange(1 - len(move.df), 1))
        source = move.df.source.iloc[0]
        for marker in MARKERS.split():
            data.setdefault((marker, source), []).append(move.trajectory(marker))

    # next, compute mean and stderr for every time step approaching targets.
    # group again by marker and source cube.
    agg = {}
    for key, dfs in data.items():
        keys = list(range(len(dfs)))
        merged = pd.concat(dfs, axis=1, keys=keys).groupby(axis=1, level=1)
        agg[key] = merged.mean(), merged.std() / np.sqrt(merged.size())

    with lmj.plot.axes(spines=True) as ax:
        ts = np.arange(-num_frames, 0)
        for marker in reversed(MARKERS.split()):
            for (m, s), (mean, stderr) in agg.items():
                if m == marker:
                    ax.plot(ts, stderr.sum(axis=1)[-num_frames:], color=COLORS[marker])
        ax.set_xticks(np.linspace(-num_frames, 0, 5))
        ax.set_xticklabels(np.linspace(-num_frames / FRAME_RATE, 0, 5))
        ax.set_xlabel('Time Before Touch (sec)')
        ax.set_ylabel('Summed Standard Error')

    def show(ax):
        ax.w_xaxis.set_pane_color((1, 1, 1, 1))
        ax.w_yaxis.set_pane_color((1, 1, 1, 1))
        ax.w_zaxis.set_pane_color((1, 1, 1, 1))
        ax.set_xlim(-2, 2)
        ax.set_xticks([-2, -1, 0, 1, 2])
        ax.set_xticklabels([])
        ax.set_ylim(-2, 2)
        ax.set_yticks([-2, -1, 0, 1, 2])
        ax.set_yticklabels([])
        ax.set_zlim(0, 2)
        ax.set_zticks([0, 1, 2])
        ax.set_zticklabels([])
        def render():
            lmj.cubes.plots.show_cubes(ax, targets, target_num=target)
            for (marker, source), (mean, stderr) in agg.items():
                mx, my, mz = mean.x, mean.y, mean.z
                sx, sy, sz = stderr.x, stderr.y, stderr.z
                for t in np.linspace(0, num_frames, 7).astype(int):
                    x, y, z = lmj.cubes.plots.ellipsoid(
                        [mx[-t], my[-t], mz[-t]],
                        [sx[-t], sy[-t], sz[-t]])
                    ax.plot_wireframe(x, z, y, color=COLORS[marker], alpha=0.3, lw=1)
        return render

    anim = lmj.plot.rotate_3d(
        show, output=output,
        azim=(0, 90), elev=(5, 20),
        fig=dict(figsize=(10, 4.8)),
    )
    if not output:
        lmj.plot.show()


if __name__ == '__main__':
    climate.call(main)
