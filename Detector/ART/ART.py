#!/usr/bin/env python
# from subprocess import call
from subprocess import check_call as call
import sys
sys.path.insert(0, '../..')
from Detector.mod_util import plot_points
import cPickle as pickle
import os

try:
    import matplotlib.pyplot as plt
except:
    plt = False
class ARTDetector(object):
    ROOT = '/home/wangjing/Dropbox/Research/sadit'
    HOME = ROOT + '/Detector/ART'
    inter_csv_data = HOME + '/output.csv'
    def __init__(self, desc={}):
        self.__dict__.update(desc)
        self.record_data = dict()

    def compile(self):
        call(['g++', 'ART_anomoly_linux.cpp', '-o', 'ART'])
        call(['g++', 'simple.cpp', '-o', 'parse'])

    def set_args(self, argv):
        pass

    def clean(self):
        call(['rm', 'ART'])
        call(['rm', 'parse'])

    def detect(self, data_handler):
        os.chdir(self.HOME)
        call(['./parse', '-fs', '-i', data_handler.data.f_name, '-o', self.inter_csv_data])
        call(['./ART', '-i1', self.inter_csv_data])
        os.chdir(self.ROOT)

        fid = open(self.HOME + '/anomalyTimeData.txt', 'r')
        self.ano_t = []
        while True:
            tline = fid.readline()
            if not tline: break
            self.ano_t.append(float(tline.rsplit()[0]))

        self.record_data['ano_t'] = self.ano_t


    # def plot(self, pic_show=True, pic_name=None):
    #     import matplotlib.pyplot as plt
    #     fid = open(self.HOME + '/anomalyTimeData.txt', 'r')
    #     ano_t = []
    #     while True:
    #         tline = fid.readline()
    #         if not tline: break
    #         ano_t.append(float(tline.rsplit()[0]))
    #     plt.plot(ano_t, [1] * len(ano_t), '+r')
    #     if pic_name:
    #         plt.savefig(pic_name)
    #     if pic_show:
    #         plt.show()

    def plot(self, *args, **kwargs):
        X = self.ano_t
        Y = [1] *len(X)
        plot_points(X, Y, None,
                # xlabel_=self.desc['win_type'], ylabel_= 'entropy',
                *args, **kwargs)

    def dump(self, data_name):
        pickle.dump( self.record_data, open(data_name, 'w') )
        # pickle.dump(self.__dict__, open(data_name, 'w') )

    def plot_dump(self, data_name, *args, **kwargs):
        """plot dumped data
        """
        self.record_data = pickle.load(open(data_name, 'r'))
        self.ano_t = self.record_data['ano_t']
        self.plot(*args, **kwargs)

if __name__ == "__main__":
    art = ARTDetector()
    # art.clean()
    art.compile()
    # art.detect()
    # art.plot()
