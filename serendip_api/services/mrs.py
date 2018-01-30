from time import time, sleep

from serendip_api.services.helpers import soap
from serendip_api.default_settings import MRS_BLAST_URL, SOAP_TIMEOUT, BLAST_TIMEOUT, POLL_INTERVAL
from serendip_api.types import ServiceError


def mrs_blast(sequence, database):
    jobid = soap.run(MRS_BLAST_URL, SOAP_TIMEOUT, "Blast", sequence, "blastp", database)

    t0 = time()
    while True:
        status = soap.run(MRS_BLAST_URL, SOAP_TIMEOUT, "BlastJobStatus", jobid)

        if status == 'error':
            error = soap.run(MRS_BLAST_URL, SOAP_TIMEOUT, "BlastJobError", jobid)

            raise ServiceError(error)
        elif status == 'finished':
            results = soap.run(MRS_BLAST_URL, SOAP_TIMEOUT, "BlastJobResult", jobid)
            return results['hits']
        else:
            if (time() - t0) > BLAST_TIMEOUT:
                raise TimeoutError("mrs blast took too long")
            else:
                sleep(POLL_INTERVAL)
