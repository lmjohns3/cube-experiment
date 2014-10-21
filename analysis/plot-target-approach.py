import climate
import itertools
import lmj.plot
import numpy as np
import pandas as pd

import database
import plots


@climate.annotate(
    root='read subject data from this file tree',
    pattern=('plot data from files matching this pattern', 'option'),
    markers=('plot data for these mocap markers', 'option'),
    target_num=('plot data for this target', 'option', None, int),
    approach_sec=('plot variance for N sec prior to target acquisition', 'option', None, float),
)
def main(root,
         pattern='*/*/*circuit00*.csv.gz',
         markers='13-r-fing-index 25-l-fing-index 40-r-heel 37-r-knee',
         target_num=3,
         approach_sec=2):
    data = {(m, s): [] for m in markers.split() for s in range(12)}
    num_frames = int(100 * approach_sec)
    frames = list(range(num_frames))
    target_locs = {}
    for trial in database.Experiment(root).trials_matching(pattern):
        move = trial.movement_to(target_num)
        try:
            move.normalize(frame_rate=100, order=1, accuracy=100)
        except:
            continue
        for marker, source in data:
            if all(move.df.source == source):
                arr = move.df.loc[:, marker + '-x':marker + '-z']
                data[marker, source].append(pd.DataFrame(
                    np.asarray(arr)[len(move.df) - num_frames::-1],
                    columns=list('xyz'),
                    index=frames[:len(move.df)]))
        target_locs[move.df['target'].iloc[0]] = np.asarray(move.df.ix[:, 'target-x':'target-z'])[0]
        target_locs[move.df['source'].iloc[0]] = np.asarray(move.df.ix[:, 'source-x':'source-z'])[0]
    with plots.space() as ax:
        for n, (x, y, z) in target_locs.items():
            ax.scatter(x, z, y, marker='o', s=200, c='#111111', linewidth=0, alpha=0.7)
            ax.text(x, z + 0.1, y + 0.1, str(n))
        for i, (marker, keys) in enumerate(itertools.groupby(sorted(data), lambda x: x[0])):
            for j, (_, source) in enumerate(keys):
                dfs = data[marker, source]
                if not dfs:
                    continue
                for df in dfs:
                    ax.plot(np.asarray(df.x),
                            np.asarray(df.z),
                            zs=np.asarray(df.y),
                            color=lmj.plot.COLOR11[i],
                            alpha=0.7)
                merged = pd.concat(dfs, axis=1, keys=list(range(len(dfs)))).groupby(axis=1, level=1)
                mu = merged.mean()
                sigma = merged.std()
                for t in np.linspace(0, num_frames - 1, 3).astype(int):
                    x, y, z = plots.ellipsoid([mu.x[t], mu.y[t], mu.z[t]],
                                              [sigma.x[t], sigma.y[t], sigma.z[t]])
                    ax.plot_wireframe(x, z, y, color=lmj.plot.COLOR11[i], alpha=0.7)


if __name__ == '__main__':
    climate.call(main)
