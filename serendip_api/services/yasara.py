import logging
import os
import shutil
import requests
from time import sleep
from io import BytesIO
from zipfile import ZipFile

from serendip_api.default_settings import YASARA_URL, POLL_INTERVAL
from serendip_api.types import ServiceError

_log = logging.getLogger(__name__)



def _unzip_result(response, output_path, script_file, script_args):
    _log.info("Unzipping response")
    zip_data = BytesIO()
    for chunk in response.iter_content(512):
        zip_data.write(chunk)

    zip_file = ZipFile(zip_data)
    if len(zip_file.namelist()) == 0:
        raise ServiceError("Zip file returned from yasara is empty")

    extracted_files = []
    for member in zip_file.namelist():
        filename = os.path.basename(member)
        # Skip directories. This puts all files in the root of output_dir,
        # avoiding the yasara-tmp-xxxx folder created by the service.
        if not filename:
            continue

        # Copy file (taken from zipfile's extract)
        source = zip_file.open(member)
        target = open(os.path.join(output_path, filename), "wb")
        _log.info("Extracting {}".format(os.path.join(output_path,
                                                      filename)))
        with source, target:
            shutil.copyfileobj(source, target)
        extracted_files.append(os.path.join(output_path, filename))

    # Check for error file
    # Yasara stores error during processing in a file and returns it in the
    # zip file. The name of the file used seems to change, or additional
    # names are added, in new releases of yasara, hence the loop.
    error_filenames = ['yasara.err', 'errorexit.txt']
    for error_filename in error_filenames:
        error_filepath = os.path.join(output_path, error_filename)
        if error_filepath in extracted_files:
            with open(error_filepath, "r") as f:
                content = f.read()
                _log.error("Error running yasara with script {}, data {} and arguments {}:\n{}"
                           .format(script_file, script_args, content))

                # Filter for random yasara errors:
                raise ServiceError(content)
    return extracted_files


def run_macro(script_file, script_args, output_dir):
    assert os.path.isfile(script_file)

    payload = {'script_args': script_args}
    files = {'script_file': open(script_file, 'rb')}

    base_url = YASARA_URL

    r = requests.post('{}/run/'.format(base_url), data=payload, files=files)
    r.raise_for_status()

    jobid = r.json()['id']

    while True:
        r = requests.get('{}/status/{}/'.format(base_url, jobid))
        if r.status_code == 200:
            status = r.json()['status']
            _log.debug("Status for '{}': {}".format(jobid, status))
            if status == 'SUCCESS':
                break
            elif status in ['FAILURE', 'REVOKED']:
                raise ServiceError(r.json()['message'])
            else:
                sleep(POLL_INTERVAL)

    r = requests.get('{}/result/{}.zip'.format(base_url, jobid),
                     stream=True)
    r.raise_for_status()

    _log.debug("Result will be extracted to '{}'".format(output_dir))

    return _unzip_result(r, output_dir, script_file, script_args)
