import climate
import lmj.plot
import numpy as np

import source
import plots


@climate.annotate(
    root='load experiment data from this directory',
    pattern='plot data from files matching this pattern',
    markers='plot traces of these markers',
)
def main(root, pattern='*5/*block00/*circuit00.csv.gz', markers='r-fing-index l-fing-index r-heel r-knee'):
    with plots.space() as ax:
        for t in source.Experiment(root).trials_matching(pattern):
            for i, marker in enumerate(markers.split()):
                df = t.trajectory(marker)
                ax.plot(np.asarray(df.x),
                        np.asarray(df.z),
                        zs=np.asarray(df.y),
                        color=lmj.plot.COLOR11[i],
                        alpha=0.7)
            continue
            t.realign(order=3)
            for i, marker in enumerate(markers.split()):
                df = t.trajectory(marker)
                ax.plot(np.asarray(df.x),
                        np.asarray(df.z),
                        zs=np.asarray(df.y),
                        color=lmj.plot.COLOR11[i],
                        alpha=0.7)


if __name__ == '__main__':
    climate.call(main)
