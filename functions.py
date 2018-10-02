import numpy as np
import pandas as pd
import scipy as sp
import matplotlib.pyplot as plt
from datetime import datetime
import sys



def GBM(s0, r, sigma, dt, T):
    z = np.random.normal(size = T)
    return s0*np.exp(np.cumsum((r-0.5*sigma**2)*dt + np.sqrt(dt)*z*sigma))

def meanReverting(s0, k, T):
    u = np.random.normal(size = T)
    S = [s0]
    for i in range(1,T):
        p = max(0, k*s0 + (1-k)*S[i-1] +u[i])
        S.append(p)
    return np.array(S)

def transform(p, scale):
    transformed = pd.Series()

    for i in range(p.index[-1]):
        try:
            transformed.set_value(datetime.fromtimestamp(i), list(p[i])[-1])
        except:
            pass
    return transformed.resample(scale).last()

def acf(series, lags = 30):
    pd.plotting.autocorrelation_plot(series)
    plt.ylim(-1, 1); plt.xlim(0, lags); plt.show()



def moments(r):
    mean = np.mean(r)
    var = np.var(r)
    skew = sp.stats.skew(r)
    kurtosis = sp.stats.kurtosis(r)
    return (mean, var, skew, kurtosis)


def QQ(r, title = ''):
    import scipy as sp
    sp.stats.probplot(r, dist='norm', plot = plt); plt.title('QQ-plot' + title)
    m = moments(r)
    m = [round(i,3) for i in m]
    jbp = round(sp.stats.jarque_bera(r)[1],2)
    text = ' Mean:        {} \n Variance:   {} \n Skewness: {} \n Kurtosis:    {} \n JB p-value: {}'\
    .format(m[0], m[1], m[2], m[3], jbp)
    plt.text(5,min(r), text)
    plt.show()


def infoplot(p):
    r = np.log(p/p.shift(1)).dropna()
    plt.figure()
    plt.subplot(221); plt.title('Mid Prices'); p.plot()
    plt.subplot(222);plt.title('Log-returns'); r.plot()
    plt.subplot(223);QQ(r)
    #plt.show()
    plt.figure();plt.title('Log-returns Autocorrelation'); acf(r)
    plt.show()
    plt.figure();plt.title('|Log-returns| Autocorrelation'); acf(abs(r))
    plt.show()

import re
class Reprinter:
    def __init__(self):
        self.text = ''

    def moveup(self, lines):
        for _ in range(lines):
            sys.stdout.write("\x1b[A")

    def reprint(self, text):
        # Clear previous text by overwritig non-spaces with spaces
        self.moveup(self.text.count("\n"))
        sys.stdout.write(re.sub(r"[^\s]", " ", self.text))

        # Print new text
        lines = min(self.text.count("\n"), text.count("\n"))
        self.moveup(lines)
        sys.stdout.write(text)
        self.text = text

import os
def sound(freq = 2400, duration = 0.1):
    os.system('play --no-show-progress --null --channels 1 synth %s sine %f' % (duration, freq))


def say(fraze):
    os.system('spd-say "{}"'.format(fraze))

def sayFemale(text):
    os.system('espeak -v female4 "{}" -a 150 -p 60 -s 160'.format(text) )

def sayMale(text):
    os.system('espeak -v male4 "{}" -a 150 -p 40 -s 150 -k 20'.format(text))

def sayRobot(text):
    os.system('spd-say "{}" -r -10 -p -40'.format(text))
