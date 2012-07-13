#!/usr/bin/env python

# Raja Selvaraj

# License: GPL

from __future__ import division
import numpy


class BardReader():
    """Read data and header information from files exported
    from Bard EP system"""
    def __init__(self, datafile):
        """datafile is the full path to the exported file"""
        self.datafile = datafile

        # read header
        with open(datafile) as fi:
            self.header = self.get_header(fi)

        # extraxt some header information
        self.info, amp_range = self.parse_header_info()

        with open(datafile) as fi:
            self.data = self.read_data(fi)

        # convert data values to microV
        self.data = self.in_microV(self.data, amp_range)


    def in_microV(self, data, amp_range):
        """
        convert the data values in microV
        amp_range is a list, 
            each value is the analog range in V for each channel
        """
        # 2 - extend range on either side
        # 1000 - convert to microV
        # 16 - bit depth
        print self.info
        print amp_range
        for chan in range(self.info['channelcount']):
            m = 2 * amp_range[chan] * 1000 / 2 ** 16
            data[:, chan] = data[:, chan] * m
        return data


    def get_header(self, fi):
        """fi is file object to exported text file.
        Return the header information"""
        header = []
        for l in fi:
            if not l.startswith('[Data]'):
                header.append(l)

            else:
                header.append('Last line')
                return header


    def parse_header_info(self):
        """Extract required information from the header"""
        info = {}
        info['channellabels'] = []

        # channel specific info
        amp_range = []  # ampl range

        for line in self.header:
            if line.startswith('Channels exported'):
                info['channelcount'] = int(line.split(':')[1].rstrip('\r\n'))
            elif line.startswith('Samples per channel'):
                info['samp_count'] = int(line.split(':')[1].rstrip('\r\n'))
            elif line.startswith('Start time'):
                info['starttime'] = line.lstrip('Start time:').rstrip('\r\n')
            elif line.startswith('End time'):
                info['endtime'] = line.lstrip('End time:').rstrip('\r\n')

            # extract channel labels
            elif line.startswith('Label'):
                info['channellabels'].append(line.split(':')[1].strip())
            elif line.startswith('Range'): 
                amp_range.append(float(line.split(':')[1].rstrip('mv \r\n')))

            else:
                continue

        return info, amp_range


    def read_data(self, fi):
        """Extract data into numpy array"""
        data = numpy.loadtxt(fi, dtype='float', delimiter=',',
                             skiprows=len(self.header))
        return data

    
def test():
    f =  '/data/Dropbox/work/jipmer_research/post_MI_risk/patient_data/first_case/nsr.txt'
    br = BardReader(f)

    # print br.info

    # print br.data.shape

    # print br.data

    assert br.data.shape == (br.info['samp_count'],
                              br.info['channelcount'])
    
if __name__ == '__main__':
    test()
