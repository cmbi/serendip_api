import logging
import md5


_log = logging.getLogger(__name__)


def get_sequence_hash(sequence):
    return md5.new(sequence).hexdigest()


def get_percentage_identity(blast_hit):
    if blast_hit is None or 'hsps' not in blast_hit:
        return 0.0

    identity = blast_hit['hsps'][0]['identity']
    qlength = len(blast_hit['hsps'][0]['queryAlignment']) - 1

    return identity * 100 / qlength


def get_best_pdb(hits):

    best = None
    for hit in hits:
        if best is None or \
                get_percentage_identity(hit) > get_percentage_identity(best):
            best = hit

    _log.info("selected best hit {}".format(best))
    return best
