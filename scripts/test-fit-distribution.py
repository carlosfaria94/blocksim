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


x = array([324.785,
           581.964,
           333.765,
           386.399,
           332.214,
           324.696,
           383.95,
           579.554,
           374.843,
           597.77,
           497.291,
           504.971,
           504.081,
           374.984,
           388.798,
           321.256,
           488.378,
           407.856,
           458.865,
           504.143,
           466.422,
           514.7,
           521.283,
           507.339,
           336.045,
           581.892,
           323.522,
           579.81,
           332.137,
           385.018,
           330.976,
           323.513,
           382.507,
           577.121,
           373.41,
           595.506,
           495.438,
           503.449,
           502.49,
           373.556,
           387.354,
           319.981,
           486.577,
           406.375,
           457.022,
           502.184,
           464.716,
           512.61,
           519.362,
           505.257,
           334.822,
           579.542])
dst = Distribution()
dst.Fit(x)
print(dst.Random(100))
dst.Plot(x)
