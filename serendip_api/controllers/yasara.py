import tempfile
import os
import shutil
import logging

from serendip_api.services.yasara import run_macro
from serendip_api.services.mrs import mrs_blast
from serendip_api.controllers.method import get_best_pdb
from serendip_api.controllers.muscle import muscle_align
from serendip_api.default_settings import YASARA_SEQUENCE_MACRO, YASARA_SCENE_MACRO


_log = logging.getLogger(__name__)


def get_yasara_sequence(pdbid, chain):

    output_dir = tempfile.mkdtemp()

    run_macro(YASARA_SEQUENCE_MACRO,
              "pdbid=\'{}\' chain=\'{}\'".format(pdbid, chain),
              output_dir)
    try:
        for filename in os.listdir(output_dir):
            if filename == "ProteinSequence.txt":
                with open(os.path.join(output_dir, filename), 'r') as f:
                    while True:
                        line = f.readline()
                        if 'Object' in line:
                            return f.readline()

        raise Exception("No sequence file")
    finally:
        if os.path.isdir(output_dir):
            shutil.rmtree(output_dir)


def make_yasara_scene(serendip_data):
    sequence = ""
    interface = []
    for record in serendip_data:
        sequence += record["AliSeq"]
        interface.append(record["prediction"] == "I")

    hits = mrs_blast(sequence, "pdb")
    best = get_best_pdb(hits)
    if best is None:
        return

    yasara_sequence = get_yasara_sequence(best['id'], best['sequenceId'])

    alignment = muscle_align({'q': sequence, 'y': yasara_sequence})

    _log.info("creating yasara scene with alignment:\n{}\n{}".format(alignment['q'], alignment['y']))

    output_dir = tempfile.mkdtemp()
    macro_path = tempfile.mktemp()
    scene_name = "ProteinPrediction.sce"
    try:
        with open(macro_path, 'w') as f:
            f.write("Clear\n")
            f.write("Colbg white\n")
            f.write("Fog 0\n")
            f.write("Hud Off\n")

            # Load pdb
            f.write("LoadPDB (pdbid),Download=Yes\n")
            f.write("CleanAll\n")
            f.write("DelAtom Element H\n")
            f.write("DelWaterAll\n")
            f.write("Style Backbone=Ribbon, Sidechain=Off\n")
            f.write("StickRadius 69%\n")
            f.write("DelObj !1\n")

            # Zoom in on the protein (stronger zoom for a smaller protein)
            f.write("Zoom Steps=0\n")
            f.write("Antialias 4\n")

            # Color all not-interesting objects grey
            f.write("DelMol !(chain)\n")
            f.write("NumberRes Obj (pdbid), First=1\n")
            f.write("ColorAll Grey\n")

            # Color all predicted residues
            for i in range(len(alignment['q'])):
                if alignment['y'][i] == '-' or alignment['q'][i] == '-':
                    continue

                n = len(alignment['q'][:i].replace('-', ''))

                if interface[n]:
                    f.write("ColRes %i,blue\n" % (i + 1))
                else:
                    f.write("ColRes %i,red\n" % (i + 1))

            # Save the scene to be returned by the service
            f.write("SaveSce %s" % scene_name)

        run_macro(macro_path,
            "pdbid=\'{}\' chain=\'{}\'".format(best['id'], best['sequenceId']),
            output_dir)

        for filename in os.listdir(output_dir):
            if filename == scene_name:
                return open(os.path.join(output_dir, filename), 'rb').read()
            elif filename == "yasara.log":
                _log.info(open(os.path.join(output_dir, filename), 'r').read())
            elif filename == "errorexit.txt":
                raise Exception(open(os.path.join(output_dir, filename), 'r').read())

        raise Exception("No scene file returned")
    finally:
        if os.path.isfile(macro_path):
            os.remove(macro_path)
        if os.path.isdir(output_dir):
            shutil.rmtree(output_dir)
