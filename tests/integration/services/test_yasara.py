import tempfile
import shutil
import os

from nose.tools import ok_

from serendip_api.services.yasara import run_macro
from serendip_api.default_settings import YASARA_SEQUENCE_MACRO


def test_sequence_macro():
    output_dir = tempfile.mkdtemp()
    try:
        run_macro(YASARA_SEQUENCE_MACRO, None, "pdbid=\'1crn\' chain=\'A\'", output_dir)

        ok_(len(os.listdir(output_dir)) > 0)
    finally:
        if os.path.isdir(output_dir):
            shutil.rmtree(output_dir)
