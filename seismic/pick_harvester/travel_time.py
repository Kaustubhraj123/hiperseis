from collections import defaultdict
import numpy as np
from scipy.interpolate import CloughTocher2DInterpolator
import traceback
import os
import glob

LARGE_VALUE = float(np.iinfo('i4').max)
class Phase:
    def __init__(self, tt_fn, fill_value=LARGE_VALUE):
        self.ecdists = None
        self.depths_km = None
        self.times = None
        self.dtdd = None
        self.dtdh = None
        self._fill_value = fill_value

        self.times_io = None
        self.dtdd_io = None
        self.dtdh_io = None

        self._parse_tt(tt_fn)

        # instantiate interpolators
        xg, yg = np.meshgrid(self.ecdists, self.depths_km, indexing='ij')
        points = np.vstack([xg.flatten(), yg.flatten()]).T

        vidx = ~np.isnan(self.times.flatten())

        self.times_io = CloughTocher2DInterpolator(points[vidx], self.times.flatten()[vidx], fill_value=self._fill_value)
        self.dtdd_io = CloughTocher2DInterpolator(points[vidx], self.dtdd.flatten()[vidx], fill_value=self._fill_value)
        self.dtdh_io = CloughTocher2DInterpolator(points[vidx], self.dtdh.flatten()[vidx], fill_value=self._fill_value)
    # end func

    def _parse_tt(self, tt_fn, nanval=-999.0):
        ecdists = []
        depths_km = []
        times = []
        dtdd = []
        dtdh = []
        dists_start = 0
        dists_end = 0
        depths_start = 0
        depths_end = 0
        times_start = 0
        times_end = 0
        dtdd_start = 0
        dtdd_end = 0
        dtdh_start = 0
        dtdh_end = 0

        ind = 0
        for line in open(tt_fn).readlines():
            row = line.split()
            if ' '.join(row) == '# delta samples':
                dists_start = ind + 1
            elif ' '.join(row) == '# depth samples':
                dists_end = ind - 1
                depths_start = ind + 1
            elif ' '.join(row) == \
                    '# travel times (rows - delta, columns - depth)':
                depths_end = ind - 2
                times_start = ind + 2
            elif ' '.join(row) == '# dtdd (rows - delta, columns - depth)':
                times_end = ind - 2
                dtdd_start = ind + 2
            elif ' '.join(row) == '# dtdh (rows - delta, columns - depth)':
                dtdd_end = ind - 2
                dtdh_start = ind + 2
            ind += 1
        #end for
        dtdh_end = ind - 4

        ind = 0
        for line in open(tt_fn).readlines():
            row = line.split()
            if ind in range(dists_start, dists_end+1):
                ecdists = ecdists + [float(item) for item in row if item != '']
            elif ind in range(depths_start, depths_end+1):
                depths_km = depths_km + [float(item) for item in row if item != '']
            elif ind in range(times_start, times_end+1):
                times = times + [[float(item) for item in row if item != '']]
            elif ind in range(dtdd_start, dtdd_end+1):
                dtdd = dtdd + [[float(item) for item in row if item != '']]
            elif ind in range(dtdh_start, dtdh_end+1):
                dtdh = dtdh + [[float(item) for item in row if item != '']]
            #end if
            ind += 1
        #end for

        self.ecdists = np.array(ecdists)
        self.depths_km = np.array(depths_km)
        self.times = np.array(times)
        self.dtdd = np.array(dtdd)
        self.dtdh = np.array(dtdh)

        self.times[self.times == nanval] = np.nan
        self.dtdd[self.dtdd == nanval] = np.nan
        self.dtdh[self.dtdh == nanval] = np.nan

        assert np.all(np.isnan(self.times) == np.isnan(self.dtdd))
        assert np.all(np.isnan(self.times) == np.isnan(self.dtdh))
    # end func
# end class

class TTInterpolator:
    def __init__(self):
        """
        Reads travel-time tables for various phases from models ak135 and iasp91, as found
        in iLoc source tar ball
        """
        self.fill_value = LARGE_VALUE
        self._ttt_folder = os.path.dirname(os.path.abspath(__file__)) + '/tt/'
        self.phases = defaultdict(lambda: defaultdict(list))

        # read and process tt-tables
        tt_files = glob.glob(self._ttt_folder + '/*.tab')
        models = set()
        phase_names = set()
        for fn in tt_files:
            model, phase_name, _ = os.path.basename(fn).split('.')
            phase_name = str.encode(phase_name) # convert to byte-string

            p = Phase(fn, fill_value=self.fill_value)
            self.phases[model][phase_name] = p
            models.add(model)
            phase_names.add(phase_name)
        # end for
    # end func

    def get_tt(self, phase, ecdist, depth_km, model='ak135'):
        try:
            if(type(phase) == np.ndarray):
                result = np.ones(len(phase), dtype='f4') * self.fill_value

                for cphase in self.phases[model].keys():
                    indices = np.argwhere(cphase == phase).flatten()

                    if(len(indices)):
                        result[indices] = self.phases[model][cphase].times_io(ecdist[indices],
                                                                              depth_km[indices])
                    # end if
                # end for

                return result
            else:
                result = self.fill_value
                if(phase in self.phases[model].keys()):
                    result = self.phases[model][phase].times_io(ecdist, depth_km)
                # end if
                return result
            # end if
        except Exception as e:
            print(traceback.format_exc())
            raise ValueError('Either model {} or phase not found..'.format(model))
        # end try
    # end func

    def get_dtdd(self, phase, ecdist, depth_km, model='ak135'):
        try:
            if(type(phase) == np.ndarray):
                result = np.ones(len(phase), dtype='f4') * self.fill_value

                for cphase in self.phases[model].keys():
                    indices = np.argwhere(cphase == phase).flatten()

                    if(len(indices)):
                        result[indices] = self.phases[model][cphase].dtdd_io(ecdist[indices],
                                                                             depth_km[indices])
                    # end if
                # end for

                return result
            else:
                result = self.fill_value
                if(phase in self.phases[model].keys()):
                    result = self.phases[model][phase].dtdd_io(ecdist, depth_km)
                # end if
                return result
            # end if
        except Exception as e:
            print(traceback.format_exc())
            raise ValueError('Either model {} or phase not found..'.format(model))
        # end try
    # end func

    def get_dtdh(self, phase, ecdist, depth_km, model='ak135'):
        try:
            if(type(phase) == np.ndarray):
                result = np.ones(len(phase), dtype='f4') * self.fill_value

                for cphase in self.phases[model].keys():
                    indices = np.argwhere(cphase == phase).flatten()

                    if(len(indices)):
                        result[indices] = self.phases[model][cphase].dtdh_io(ecdist[indices],
                                                                             depth_km[indices])
                    # end if
                # end for

                return result
            else:
                result = self.fill_value
                if(phase in self.phases[model].keys()):
                    result = self.phases[model][phase].dtdh_io(ecdist, depth_km)
                # end if
                return result
            # end if
        except Exception as e:
            print(traceback.format_exc())
            raise ValueError('Either model {} or phase not found..'.format(model))
        # end try
    # end func
# end class

