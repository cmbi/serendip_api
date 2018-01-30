import os
import sys
import subprocess
import tempfile

from serendip_api.default_settings import MUSCLE_EXE, SERENDIP_DIR


def muscle_align(sequences_dict):
    sys.path.append(SERENDIP_DIR)
    from sequence.entropy.lib.seq_lib import FastaParser

    input_fasta = tempfile.mktemp()
    output_fasta = tempfile.mktemp()
    try:
        with open(input_fasta, 'w') as f:
            for id_ in sequences_dict:
                f.write(">%s\n%s\n" % (id_, sequences_dict[id_]))

        cmd = [MUSCLE_EXE, "-in", input_fasta, "-out", output_fasta]
        subprocess.call(cmd)
        return {sequence.Label: sequence.Sequence
                for sequence in FastaParser(open(output_fasta, 'r'))}
    finally:
        for path in [input_fasta, output_fasta]:
            if os.path.isfile(path):
                os.remove(path)
