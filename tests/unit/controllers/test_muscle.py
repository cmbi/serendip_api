from nose.tools import eq_

from serendip_api.controllers.muscle import muscle_align


def test_muscle_align():
    input_ = {'1': 'TTTTATAAG',
              '2': 'TTTTTATAAG'}
    output = muscle_align(input_)

    eq_(output['1'], '-TTTTATAAG')
