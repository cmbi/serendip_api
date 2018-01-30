import os
import sys
import shutil
import subprocess
import tempfile
import logging

from celery import current_app as celery_app
from filelock import FileLock

from serendip_api.controllers.muscle import muscle_align
from serendip_api.controllers.yasara import make_yasara_scene
from serendip_api.controllers.method import get_sequence_hash

settings = {}
config_path = os.path.join("serendip_api", "default_settings.py")
with open(config_path) as config_file:
    exec(compile(config_file.read(), config_path, 'exec'), settings)

from serendip_api.controllers.serendip import parse_serendip_results


_log = logging.getLogger(__name__)


@celery_app.task()
def netsurf_hit(fasta_string):

    out_dir = tempfile.mkdtemp()
    try:
        input_fasta_path = os.path.join(out_dir, 'input.fa')
        output_hits_path = os.path.join(out_dir, 'output.myrsa')

        with open(input_fasta_path, 'w') as f:
            f.write(fasta_string)

        cmd = [settings["NETSURF_EXE"],
               "-i", input_fasta_path,
               "-d", settings["NR70_DB"], "-a",
               "-o", output_hits_path]
        _log.info(cmd)
        subprocess.call(cmd)

        # clean up 'X-es' in output, so whitespace separated columns are retained:
        cmd = ['/bin/sed', 's/^  X/- X/']
        return subprocess.check_output(cmd, stdin=open(output_hits_path, 'r'))
    finally:
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)


@celery_app.task()
def predict(input_sequence):
    sys.path.append(settings["SERENDIP_DIR"])
    from sequence.entropy.lib.seq_lib import FastaParser
    from Bio.Blast import NCBIStandalone

    sequence_hash = get_sequence_hash(input_sequence)
    results_path = os.path.join(settings["RESULTS_DIR"], sequence_hash)
    lock_path = results_path + ".lock"

    with FileLock(lock_path):

        if os.path.isfile(results_path):
            return parse_serendip_results(open(results_path, 'r').read())

        input_id = 'input'
        out_dir = tempfile.mkdtemp()

        try:
            out_file = os.path.join(out_dir, 'output.myrsa')
            input_fasta_path = os.path.join(out_dir, input_id + '.fa')

            # Netsurf
            open(input_fasta_path, 'w').write(">%s\n%s" % (input_id, input_sequence))
            cmd = [settings["NETSURF_EXE"],
                   "-i", input_fasta_path,
                   "-d", settings["NR70_DB"], "-a", "-k",
                   "-T", out_dir, "-o", out_file]
            _log.info(cmd)
            subprocess.call(cmd)

            blast_parser = NCBIStandalone.PSIBlastParser()
            blast_record = blast_parser.parse(open(os.path.join(out_dir, input_id + '.blastout'), 'r'))
            if blast_record.rounds <= 0:
                raise Exception("no netsurf hits")
            hit_titles = [alignment.title[1:]
                          for alignment in blast_record.rounds[-1].alignments]

            id_path = os.path.join(out_dir, input_id + '.blastout_id')
            with open(id_path, 'w') as f:
                for hit_title in hit_titles:
                    f.write(hit_title + '\n')

            blast_hits_path = os.path.join(out_dir, 'output_seqs.fa')
            cmd = [settings["FASTACMD_EXE"],
                   "-d", settings["NR70_DB"],
                   '-i', id_path,
                   '-o', blast_hits_path]
            _log.info(cmd)
            result = subprocess.call(cmd)


            if result == 0:  # We have blast hits

                # Netsurf on hits
                netsurf_append_path = os.path.join(out_dir, 'output_other.myrsa')
                subtasks = [netsurf_hit.delay(str(seq))
                            for seq in FastaParser(open(blast_hits_path, 'r'))]

                with open(netsurf_append_path, 'w') as f:
                    for subtask in subtasks:
                        f.write(subtask.get())

                # Append input sequence to blast hits for alignment as input for entropy and DynaMine
                with open(blast_hits_path, 'a') as f:
                    f.write('>input\n' + input_sequence + '\n')

                # Make alignment using muscle
                alignment_path = os.path.join(out_dir, "output.ali")
                cmd = [settings["MUSCLE_EXE"],
                       "-in", blast_hits_path,
                       "-out", alignment_path]
                _log.info(cmd)
                subprocess.call(cmd)

            else:  # No blast hits

                alignment_path = input_fasta_path
                blast_hits_path = input_fasta_path


            # Alignment position entropies
            entropy_path = os.path.join(out_dir, "output.entropy")
            hit_sequences = FastaParser(open(alignment_path, 'r'))
            hit_sequences.frequencies().normalize()
            hit_entropies = hit_sequences.frequencies().entropies()
            with open(entropy_path, 'w') as f:
                n = 0
                for entropy in hit_entropies:
                    n += 1
                    f.write(str(n) + ' ' + str(entropy) + '\n')


            # Run dynamine on each sequence
            dynamine_fasta_path = os.path.join(out_dir, "output_seq.fasta")
            for seq in FastaParser(open(blast_hits_path, 'r')):
                # We use this file name, to avoid confusing the rest of the script:
                with open(dynamine_fasta_path, 'w') as f:
                    f.write(str(seq))
                cmd = [settings["DYNAMINE_EXE"], "-a", dynamine_fasta_path]
                _log.info(cmd)
                subprocess.call(cmd, env=dict(os.environ,
                                              **{"PYTHONPATH":"/usr/local/lib/python2.7/site-packages/"}))


            # Run prediction script
            result_testing_path = os.path.join(settings["SERENDIP_DIR"], "sequence", "Result_Testing")
            combined_path = os.path.join(settings["SERENDIP_DIR"], "sequence", "five_models_combined")
            dynamine_path = os.path.splitext(dynamine_fasta_path)[0]
            cmd = [settings["RSCRIPT_EXE"], settings["RF_SCRIPT"], input_id,
                   alignment_path, entropy_path, netsurf_append_path,
                   dynamine_path, out_file, result_testing_path, combined_path]
            _log.info(cmd)
            os.chdir(out_dir)
            subprocess.call(cmd)

            os.listdir(out_dir)

            output_result_path = os.path.join(out_dir, input_id + '.out')
            shutil.copyfile(output_result_path, results_path)

            return parse_serendip_results(open(results_path, 'r').read())

        finally:
            if os.path.isdir(out_dir):
                shutil.rmtree(out_dir)


@celery_app.task()
def yasara_scene(serendip_data):
    _log.info("generating scene for data {}".format(serendip_data))

    sequence = ""
    for record in serendip_data:
        sequence += record["AliSeq"]

    sequence_hash = get_sequence_hash(sequence)

    scene_path = os.path.join(settings["RESULTS_DIR"], sequence_hash + ".sce")
    lock_path = scene_path + ".lock"

    if os.path.isfile(scene_path):
        return open(scene_path, 'rb').read()
    else:
        with FileLock(lock_path):
            scene_data = make_yasara_scene(serendip_data)

            open(scene_path, 'wb').write(scene_data)
            return scene_data
