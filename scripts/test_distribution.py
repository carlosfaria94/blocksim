from matplotlib import pyplot as plt
from scipy import array, stats


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
            dist = getattr(stats, dist_name)
            param = dist.fit(y)

            self.params[dist_name] = param
            # Applying the Kolmogorov-Smirnov test
            D, p = stats.kstest(y, dist_name, args=param)
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
            dist = getattr(stats, dist_name)
            return dist.rvs(*param[:-2], loc=param[-2], scale=param[-1], size=n)
        else:
            raise ValueError('Must first run the Fit method.')

    def Plot(self, y):
        x = self.Random(n=len(y))
        plt.hist(x, alpha=0.5, label='Fitted')
        plt.hist(y, alpha=0.5, label='Actual')
        plt.legend(loc='upper right')
        plt.show()


def get_from_file(file_path):
    times = []
    with open(file_path) as f:
        for t in f:
            print(int(t))
            times.append(int(t))
    return array(times)


#x = get_from_file('')
#x = array([ ])
# print(x)
dst = Distribution()
# dst.Fit(x)
rands = dst.Random(100)
print(rands)
for rand in rands:
    if rand < 0:
        print(f'ALERT! {rand} negative delays')
# dst.Plot(x)
