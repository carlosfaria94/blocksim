import scipy
import scipy.stats
import matplotlib
import matplotlib.pyplot as plt
import re
from scipy import array
import numpy as np


class Distribution(object):

    def __init__(self, dist_names_list=[]):
        self.dist_names = ['norm', 'lognorm', 'expon',
                           'beta', 'gamma', 'exponweib', 'invgamma']
        self.dist_results = []
        self.params = {}

        self.DistributionName = ""
        self.PValue = 0
        self.Param = None

        self.isFitted = False

    def Fit(self, y):
        self.dist_results = []
        self.params = {}
        for dist_name in self.dist_names:
            dist = getattr(scipy.stats, dist_name)
            param = dist.fit(y)

            self.params[dist_name] = param
            # Applying the Kolmogorov-Smirnov test
            D, p = scipy.stats.kstest(y, dist_name, args=param)
            self.dist_results.append((dist_name, p))

        print('Kolmogorov-Smirnov test', self.dist_results)

        # select the best fitted distribution
        sel_dist, p = (max(self.dist_results, key=lambda item: item[1]))
        # store the name of the best fit and its p value
        self.DistributionName = sel_dist
        self.PValue = p
        self.Param = self.params[sel_dist]

        print('The distribution that fit:', self.DistributionName)
        print('Input parameter for the distribution:', self.Param)

        self.isFitted = True
        return self.DistributionName, self.PValue

    def Random(self, n=1):
        if self.isFitted:
            dist_name = self.DistributionName
            param = self.Param
            # initiate the scipy distribution
            dist = getattr(scipy.stats, dist_name)
            return dist.rvs(*param[:-2], loc=param[-2], scale=param[-1], size=n)
        else:
            raise ValueError('Must first run the Fit method.')

    def Plot(self, y):
        x = self.Random(n=len(y))
        plt.hist(x, alpha=0.5, label='Fitted')
        plt.hist(y, alpha=0.5, label='Actual')
        plt.legend(loc='upper right')
        plt.show()


def get_pings():
    pings = []
    with open("Ohio-ping-Ireland-jun-22.txt") as f:
        for line in f:
            for ping in re.findall(r'time=\d+.\d', line):
                pings.append(float(ping[5:]))

    _pings = array(pings)
    print('Ping values:', _pings)
    return _pings


x = array([44.2066,
           44.8232,
           52.965,
           49.1873,
           41.8693,
           40.9818,
           66.2478,
           101.27,
           40.7525,
           138.088,
           137.413,
           82.7867,
           137.514,
           44.1747,
           47.9714,
           113.19,
           91.8037,
           45.1296,
           39.4183,
           42.5647,
           40.895,
           87.5489,
           43.0646])
dst = Distribution()
dst.Fit(x)
print(dst.Random(100))
# dst.Plot(x)
