from __future__ import division
import scipy
import scipy.signal
import pylab
import commands


def _norm_dot_product(a,b):
    """Will return normalized dot product for two vectors"""
    # TODO: Needs better documentation
    anorm = a/(scipy.dot(a,a)**0.5)
    bnorm = b/(scipy.dot(b,b)**0.5)
    return scipy.dot(anorm,bnorm)

def _ms_to_samples(ms, samplingrate):
    """convert interval in ms to number of samples.
    samplingrate is samples / second"""
    return samplingrate * ms / 1000

def _lfilter_zi(b,a):
    #compute the zi state from the filter parameters. 
    #Based on:
    # Fredrik Gustafsson, Determining the initial states in forward-backward 
    # filtering, IEEE Transactions on Signal Processing, pp. 988--992, April 1996, 
    # Volume 44, Issue 4
    n=max(len(a),len(b))
    zin = (scipy.eye(n-1) - scipy.hstack( (-a[1:n,scipy.newaxis],
                                 scipy.vstack((scipy.eye(n-2), scipy.zeros(n-2))))))
    zid=  b[1:n] - a[1:n]*b[0]
    zi_matrix=scipy.linalg.inv(zin)*(scipy.matrix(zid).transpose())
    zi_return=[]
    #convert the result into a regular array (not a matrix)
    for i in range(len(zi_matrix)):
      zi_return.append(float(zi_matrix[i][0]))

    return scipy.array(zi_return)

def filtfilt(b,a,x):
    """
    Filter with given parameters forward and in reverse to eliminate
    phase shifts.
    In addition, initial state is calculated with lfilter_zi and 
    mirror images of the sample are added at end and beginning to
    remove edge effects.
    Must be a one-dimensional array only.
    """
    #For now only accepting 1d arrays
    ntaps=max(len(a),len(b))
    edge=ntaps*3

    if x.ndim != 1:
        raise ValueError, "Filtfilt is only accepting 1 dimension arrays."

    #x must be bigger than edge
    if x.size < edge:
        raise ValueError, "Input vector needs to be bigger than 3 * max(len(a),len(b)."

    if len(a) < ntaps:
        a=scipy.r_[a,scipy.zeros(len(b)-len(a))]

    if len(b) < ntaps:
        b=scipy.r_[b,scipy.zeros(len(a)-len(b))]

    zi=_lfilter_zi(b,a)

    #Grow the signal to have edges for stabilizing 
    #the filter with inverted replicas of the signal
    s=scipy.r_[2*x[0]-x[edge:1:-1],x,2*x[-1]-x[-1:-edge:-1]]
    #in the case of one go we only need one of the extrems 
    # both are needed for filtfilt

    (y,zf)=scipy.signal.lfilter(b,a,s,-1,zi*s[0])

    (y,zf)=scipy.signal.lfilter(b,a,scipy.flipud(y),-1,zi*y[-1])

    return scipy.flipud(y[edge-1:-edge+1])

def _rms(vector):
    """returns the root mean square"""
    return scipy.sqrt(scipy.mean(vector**2))


class ECG():
    def __init__(self, ecg, samplingrate = 1000):
        self.ecg = ecg
        self.samplingrate = samplingrate
    

    def remove_baseline(self, anchorx, window):
        """Remove baseline wander by subtracting a cubic spline.
        ecg is vector representing one ecg channel.
        anchorx is a vector of isoelectric points (usually qrs onset -20ms)
        window is width of window to use (in ms) for averaging the amplitude at anchors"""
        windowwidth = _ms_to_samples(window, self.samplingrate) / 2
    
        #Do we have enough points before first anchor to use it
        if anchorx[0] < windowwidth:
            anchorx = anchorx[1:]

        # subtract dc
        self.ecg -= scipy.mean(self.ecg[anchorx[:]]) 

        # amplitudes for anchors
        # window is zero, no averaging
        if windowwidth == 0:
            anchory = scipy.array([self.ecg[x] for x in anchorx])
        # or average around the anchor
        else:
            anchory = scipy.array([scipy.mean(self.ecg[x-windowwidth:x+windowwidth])
                                   for x in anchorx])
            
        # x values for spline that we are going to calculate
        splinex = scipy.array(range(len(self.ecg)))

        # calculate cubic spline fit
        tck = scipy.interpolate.splrep(anchorx, anchory)
        spliney = scipy.interpolate.splev(splinex, tck)

        # subtract the spline
        self.ecg -= spliney
    
        return
    

        def write_ann(self, annfile):
            """Write an annotation file for the QRS onsets in a format
            that is usable with wrann"""
            fi = open(annfile, 'w')
            for qrspeak in self.QRSpeaks:
                fi.write('%s %s %s %s %s %s\n' %(self._sample_to_time(qrspeak), qrspeak, 'N', 0, 0, 0))
            fi.close()


def test_remove_baseline():
    """test for remove_baseline function
    """
    testsignal = scipy.sin(scipy.arange(0,2*scipy.pi,0.01))
    npoints = len(testsignal)
    pylab.plot(testsignal, 'b')

    anchors = range(0,len(testsignal), len(testsignal)//8)
    window = 0

    ecg = ECG(testsignal, 1)
    rms_with_baseline = _rms(ecg.ecg)

    ecg.remove_baseline(anchors, window)
    rms_without_baseline = _rms(ecg.ecg)

    assert rms_without_baseline / rms_with_baseline < 0.01


if __name__ == '__main__':
    test_remove_baseline()
