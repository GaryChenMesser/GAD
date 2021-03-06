""" Robust Methods
"""
from __future__ import print_function, division, absolute_import
import itertools, copy
# import cPickle as pk
from ..util import zload
from ..util import save_csv, plt
from .mod_util import plot_points
from ..util import del_none_key

from . import StoDetector
from .DetectorLib import I1, I2, adjust_mat
# from .PLIdentify import PL_identify
from .PLRefine import HeuristicRefinePL

###### added by Jing Zhang (jingzbu@gmail.com)
import numpy as np
from numpy import linalg as LA
# from math import sqrt
# from scipy.stats import chi2
# from matplotlib.mlab import prctile
##############################################


def cal_I_rec(ref_pool, fb_PL, enable=None):
    """ calculate model-free and model-based fitness value with each reference
    PL in the pool

    Parameters
    ---------------
    ref_pool : dict
        a diction of (name, ref_PL)

    fb_PL : tuple
        model free and model based PL

    enable : list of list, optional
        enable[0][i] == True means the ith model-free reference PL

    Returns
    --------------
    I_rec : nx2 np.array
        n is the number of reference empirical measure
        the first column is the I1 and the second column is I2

    """
    d_pmf, d_Pmb = fb_PL

    print('The model-based empirical measure is ')
    print(d_Pmb)
    print('-' * 10)

    n = len(ref_pool)
    if enable is None:
        enable = [[True] * n for i in [1, 2]]

    I_rec = np.zeros((n, 2))
    i = -1
    for _, ref_PL in ref_pool.iteritems():
        i += 1
        if ref_PL is None:
            I_rec[i, :] = [float('inf'), float('inf')]
            continue

        # pmf, Pmb = ref_PL
        _, Pmb = ref_PL

        print("The model-based PL #%d is "%i)
        print(Pmb)

        # I_rec[i, 0] = I1(d_pmf, pmf) if enable[0][i] else float('inf')
        I_rec[i, 1] = I2(d_Pmb, Pmb) if enable[1][i] else float('inf')

        print("The divergence between the model-based empirical measure and the PL #%d is %f"%(i, I_rec[i, 1]))
        print('-' * 20)

    return I_rec

class PLManager(object):
    """ Probability Law Manager

    Parameters
    ---------------
        ref_file: data handler class
            data_handler class
    Returns
    --------------
    """

    def __init__(self, ref_file):
        self.ref_file = ref_file
        self.det = dict()
        self.det_para = dict()
        self.det_type = dict()
        self.det_flag = dict()

        self.ref_pool = dict()

    def register(self, alg_name, alg, para, type ='dynamic',
            para_type='izip'):
        """ register a algorithm

        Parameters
        --------------------
        alg_name : str
            name of the algorithm
        alg : a class object
            require *cal_norm_em* function.
        para : dict
            dict of all parameters. All the combinations
            of parameters will be tried
        type_ : {'static', 'dynamic'}
            'static' :
        para_type : {'izip', 'product'}
            define how to generate parameter combinations

        Returns
        --------------------
        None

        Notes
        --------------------

        """
        self.det[alg_name] = alg

        # store det_para
        para = del_none_key(para)
        self.det_para[alg_name] = (para.keys(), \
                getattr(itertools, para_type)(*para.values()))

        self.det_type[alg_name] = type

    def _loop_para(self, alg_name, int_rg):
        """ loop through the possible parameters for alg_name

        Parameters
        -------------------
            alg_name : str
                name of the algorithm
            int_rg : list
                range of data that will be used to calculated empirical measure

        Return
        -------------------
        None

        Notes
        -------------------
        the calculated empirical measure will be stored in a dictionary
        key is the (alg_name, para_str), where para_str is a str representing
        all the para combination.

        If the type of the algorithm is 'static', then the empirical measure
        will be only calculated for one time.

        """
        d_obj = self.det[alg_name]
        d_obj.rg = int_rg
        d_obj.ref_file = self.ref_file

        para_names, para_values_gen = self.det_para[alg_name]
        for para_values in para_values_gen:
            cp = dict(zip(para_names, para_values)) # parameters
            key = (alg_name, str(cp)) # key
            self.ref_pool[key] = d_obj.cal_norm_em(norm_em=None, **cp)

    def process_data(self, int_rg=None):
        """ process data using different methods and

        Parameters
        ---------------------

        int_rg : list, optional
            Current range. It is helpful when the reference empirical measure
            is dependent on the detection place.

        Notes
        ---------------------
            1. store the empirical measure calculated
            2. calculate the entropy of each empirical measure

        """
        # win_size = self.desc['win_size']
        # if int_rg is None: int_rg = [0, win_size]

        # """specify the method and the parameters will be used"""
        for alg_name in self.det.keys():
            if self.det_type[alg_name] == 'static' and \
                self.det_flag.get(alg_name):
                    continue

            self.det_flag[alg_name] = True
            self._loop_para(alg_name, int_rg)

        return self.ref_pool

    # def select(self, I_rec, lamb):
    #     n = len(I_rec) # window size
    #     m = I_rec[0].shape[0] # no. of PLs
    #     mf_D = np.zeros((m, n))
    #     mb_D = np.zeros((m, n))
    #     for j in xrange(n):
    #         for i in xrange(m):
    #             mf_D[i, j] = I_rec[j][i, 0]
    #             mb_D[i, j] = I_rec[j][i, 1]
    #     return PL_identify(mf_D, lamb), PL_identify(mb_D, lamb)

    def select(self, I_rec, lamb_mf, lamb_mb):
        # n = len(I_rec) # window size
        # m = I_rec[0].shape[0] # no. of PLs
        n = I_rec[0].shape[0] # no. of candidate PLs
        m = len(I_rec) # no. of windows
        mf_D = np.zeros((m, n))
        mb_D = np.zeros((m, n))
        for j in xrange(n):
            for i in xrange(m):
                mf_D[i, j] = I_rec[i][j, 0]
                mb_D[i, j] = I_rec[i][j, 1]
        print('-' * 50)
        print(mf_D)
        print('-' * 50)
        print(mb_D)
        print('-' * 50)

        gam = 50
        r = 0.5
        epsi = 0.001
        return HeuristicRefinePL(mf_D, lamb_mf, gam, r, epsi), \
                HeuristicRefinePL(mb_D, lamb_mb, gam, r, epsi)

class RobustDetector(StoDetector.FBAnoDetector):
    """ Robust Detector is designed for dynamic network environment
    """
    def __init__(self, desc):
        StoDetector.FBAnoDetector.__init__(self, desc)
        self._init_record()

    def _init_record(self):
        self.record_data = dict(entropy=[], winT=[], threshold=[], em=[])
        self.record_data['select_model'] = []
        self.record_data['I_rec'] = []

    def init_parser(self, parser):
        super(RobustDetector, self).init_parser(parser)
        parser.add_argument('-r', '--ref_scheck', default=None, type=str,
                help="""['dump <file>', 'load <file>']. whether to load the precomputed
                reference self check data or calculate and dump it. If <file> is
                not specfied, its default value is
                "desc['dump_folder']/PLManager_scheck.pk" """)

        parser.add_argument('--days', default=7, type=float,
                help="""number of days the simulated test data lasts; default=7""")

        parser.add_argument('--alpha', default=0.5, type=float,
                help="""weight of minimum threshold determining the up-bound of nominal cross-entropy;
                should be within (0, 1), default=0.5""")

        parser.add_argument('--lamb', default=0, type=float,
                help="""manual up-bound for nominal cross entropy; only when lamb>0, use its value;
                has higher priority than alpha""")

        parser.add_argument('--ref_data', default=None, type=str,
                help="""name for reference file""")

    def detect(self, data_file, ref_file=None):
        if ref_file is None:
            raise Exception('reference file must be specified for robust '
            'detector')
        register_info = self.desc['register_info']
        ref_scheck = self.desc['ref_scheck']
        # lamb = self.desc['lamb']
        # StoDetector.FBAnoDetector.save_threshold(self, data_file)
        # print(np.array(self.record_data['threshold']).shape)
        rg_type = self.desc['win_type']
        max_detect_num = self.desc['max_detect_num']

        self.data_file = data_file
        self.ref_file = data_file if ref_file is None else ref_file
        # import ipdb;ipdb.set_trace()
        # self.ref_file = ref_file
        # self.norm_em = self.get_em(rg=nominal_rg, rg_type=rg_type)
        self.norm_em = self.cal_norm_em()
        # self.desc['norm_em'] = self.norm_em
        # print(self.norm_em)
        # assert(1 == 2)
        pmf, Pmb = self.norm_em
        self.mu = adjust_mat(Pmb)
        # print(self.mu)
        # mu = np.array(mu)
        mu = self.mu
        N, _ = mu.shape
        assert(N == _)

        ########### Added by Jing Zhang (jingzbu@gmail.com)
        # for model-based method only
        Q = self.Q_est(self.mu)
        Nq, _ = Q.shape
        assert(Nq == _)
        #assert(Nq == cardinality)
        P = self.P_est(Q)  # Get the pair (new) transition matrix
        k = 1000
        PP = LA.matrix_power(P, k)
        mu = PP[0, :]
        mu = mu.reshape(N, N)
        self.mu = mu

        self.G = self.G_est(Q)  # Get the gradient estimate
        self.H = self.H_est(self.mu)  # Get the Hessian estimate
        Sigma = self.Sigma_est(P, self.mu)  # Get the covariance matrix estimate

        # Generate samples of W
        self.SampleNum = 1000
        W_mean = np.zeros((1, N**2))
        self.W = np.random.multivariate_normal(W_mean[0, :], Sigma, (1, self.SampleNum))

        lamb_mf, lamb_mb = zip(*StoDetector.FBAnoDetector.save_threshold(self, data_file))
        # lamb_mf = np.amax((np.array(lamb_mf)))
        # lamb_mb = np.amax((np.array(lamb_mb)))
        alpha = self.desc['alpha']
        lamb_mf = alpha * np.amin((np.array(lamb_mf))) + (1 - alpha) * np.amax((np.array(lamb_mf)))
        lamb_mb = alpha * np.amin((np.array(lamb_mb))) + (1 - alpha) * np.amax((np.array(lamb_mb)))
        if self.desc['lamb'] > 0:
            lamb_mb = self.desc['lamb']
        # lamb_mb = 0.0379389039126
        # print(lamb_mf)
        print('The parameter lambda for model-based PL refinement is %f'%lamb_mb)
        # assert(1 == 2)
        self.plm = PLManager(ref_file)

        for method, prop in register_info.iteritems():
            det = getattr(StoDetector, method)(copy.deepcopy(self.desc))
            self.plm.register(method, det, **prop)

        self.ref_pool = self.plm.process_data()

        self.PL_enable = None
        if lamb_mf > 0 and lamb_mb > 0: # enable Probability Law Identification
            get_filepath = lambda s: ' '.join(s.split()[1:])
            rs_file = get_filepath(ref_scheck)

            # for backward compatibility
            if not rs_file and self.desc.get('dump_folder'):
                rs_file = self.desc['dump_folder'] + 'PLManager_scheck.pk'

            if ref_scheck.startswith('dump'):
                StoDetector.FBAnoDetector.detect(self, ref_file, ref_file)
                ref_I_rec = self.record_data['I_rec']
                self.dump(rs_file)
                self._init_record()
            elif ref_scheck.startswith('load'):
                data = zload(rs_file)
                ref_I_rec = data['I_rec']
            else:
                raise Exception('unknown ref_scheck operation')

            self.PL_enable = self.plm.select(ref_I_rec, lamb_mf, lamb_mb)
            # print(self.PL_enable)
            # print(self.PL_enable[1])
            # if self.PL_enable[0] is None or self.PL_enable[1] is None:
            if self.PL_enable[1] is None:
                raise Exception('lamb is too small, probably you have too '
                        'little candidates')
        StoDetector.FBAnoDetector.detect(self, data_file, ref_file)

    def I(self, em, **kwargs):
        """ calculate

        Notes
        --------------------------
        Suppose we have empirical NE_i calculated by detector i, i=1,...,N
        the output I = min(I(E, NE_i)) for i =1,...,N

        """
        # self.process_data(self.ref_file, self.rg)
        # self.ref_pool = self.plm.process_data(self.rg, self.PL_selection)

        # d_pmf, d_Pmb= em
        self.desc['em'] = em

        I_rec = cal_I_rec(self.ref_pool, em, self.PL_enable)

        res = np.min(I_rec, axis=0)
        model = np.nanargmin(I_rec, axis=0)
        self.record_data['select_model'].append(model)
        self.record_data['I_rec'].append(I_rec)

        print('I matrix: \n', I_rec)
        print('min entropy: \n', res)
        # print('model-free model: ', model[0], ' description: ',
        #         self.ref_pool.keys()[model[0]])
        print('model-based model: ', model[1], ' description: ',
                self.ref_pool.keys()[model[1]])
        print('--------------------')
        return res

    def save_addi_info(self, **kwargs):
        super(RobustDetector, self).save_addi_info()
        self.record_data['ref_pool'] = self.ref_pool

    # plot module added by Jing Zhang (jingzbu@gmail.com)
    def plot(self, far=None, figure_=None,
            # title_='model based',
            pic_name=None, pic_show=False, csv=None,
            *args, **kwargs):

        # Please see https://codeyarns.com/2014/10/27/how-to-change-size-of-matplotlib-plot/
        # Get current size
        fig_size = plt.rcParams['figure.figsize']

        # Set figure width to 12.0 and height to 6.0
        fig_size[0] = 12.0
        fig_size[1] = 6.0
        plt.rcParams['figure.figsize'] = fig_size

        if not plt: self.save_plot_as_csv()

        rt = self.record_data['winT']
        rt = [t/3600 for t in rt]
        mf, mb = zip(*self.record_data['entropy'])
        # threshold_mf, threshold_mb = zip(*self.record_data['threshold'])
        _, threshold_mb = zip(*self.record_data['threshold'])
        alpha = self.desc['alpha']
        threshold_mb = np.multiply(threshold_mb, (1 + 2 * abs(alpha)))

        if csv:
            save_csv(csv, ['rt', 'mf', 'mb', 'threshold_mb'], rt, mf, mb, threshold_mb)

        if figure_ is None: figure_ = plt.figure()
        # import ipdb;ipdb.set_trace()
        plot_points(rt, mb, threshold_mb,
                figure_ = figure_,
                xlabel_=self.desc['win_type'], ylabel_= 'entropy',
                # title_ = title_,
                pic_name=None, pic_show=False,
		lw=self.desc['lw'],
                *args, **kwargs)
        plt.xlim([0, 24 * self.desc['days']])
        plt.ylabel('divergence')
        plt.xlabel('time (h)')
        if pic_name and not plt.__name__.startswith("guiqwt"): plt.savefig(pic_name)
        if pic_show: plt.show()
