import climate
import os
import pandas as pd

logging = climate.get_logger('source')


class Subject:
    '''Encapsulates data from a single subject.

    Attributes
    ----------
    root : str
        The root filesystem path containing this subject's data.
    blocks : list of `Block`
        A list of the blocks for this subject.
    '''

    def __init__(self, root):
        self.root = root
        self.blocks = [Block(self, f) for f in os.listdir(root)]
        logging.info('%s: loaded subject with %d blocks',
                     os.path.basename(root), len(self.blocks))

    def load(self, interpolate=True):
        [b.load(interpolate) for b in self.blocks]


class Block:
    '''Encapsulates data from a single block (from one subject).

    Parameters
    ----------
    subject : `Subject`
        The subject whose block this is.
    basename : str
        The filesystem directory containing the data for this block.

    Attributes
    ----------
    subject : `Subject`
        The subject whose block this is.
    basename : str
        The filesystem directory containing the data for this block.
    trials : list of `Trial`
        A list of the trials for this subject.
    '''

    def __init__(self, subject, basename):
        self.subject = subject
        self.basename = basename
        self.trials = [Trial(self, f) for f in os.listdir(self.root)]
        logging.info('%s: loaded block with %d trials',
                     self.basename, len(self.trials))

    @property
    def root(self):
        return os.path.join(self.subject.root, self.basename)

    def load(self, interpolate=True):
        [t.load(interpolate) for t in self.trials]


class Trial:
    '''Encapsulates data from a single trial (from one block of one subject).

    Parameters
    ----------
    block : `Block`
        The block containing this trial.
    basename : str
        The CSV file containing the data for this trial.

    Attributes
    ----------
    block : `Block`
        The block containing this trial.
    basename : str
        The name of the CSV file containing the trial data.
    df : pandas.DataFrame
        Data for this trial.
    '''

    def __init__(self, block, basename):
        self.block = block
        self.basename = basename
        self.df = None

    @property
    def path(self):
        return os.path.join(self.block.root, self.basename)

    @property
    def markers(self):
        for i, h in enumerate(self.df.columns):
            if h[:2].isdigit() and h.endswith('-x'):
                yield i, h[3:-2]

    def marker(self, name):
        markers = {h: i for i, h in self.markers}
        index = markers[name]
        return [self.df.iloc[:, i] for i in range(index, index + 3)]

    def frame_for_contact(self, target):
        idx = self.df.target.where(target)
        return idx[-1]

    def clear(self):
        self.df = None

    def load(self, interpolate=True):
        self.df = pd.read_csv(self.path, compression='gzip')
        if interpolate:
            self.interpolate()
        logging.info('%s: loaded trial %s', self.basename, self.df.shape)

    def interpolate(self):
        '''Interpolate missing mocap data.'''
        idx = [i for i, _ in self.markers]
        for c in range(idx[0], idx[-1] + 1, 4):
            markers = self.df.ix[:, c:c+4]
            markers[markers.ix[:, -1] < 0] = float('nan')
            self.df.ix[:, c:c+4] = markers.interpolate()
