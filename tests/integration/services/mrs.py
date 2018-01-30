from nose.tools import ok_, eq_

from serendip_api.services.mrs import mrs_blast


def test_mrs_blast():
    hits = mrs_blast("TTCCPSIVARSNFNVCRLPGTPEAICATYTGCIIIPGATCPGDYAN", 'pdb')

    eq_(type(hits), list)
    ok_(len(hits) > 0)
