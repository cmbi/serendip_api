import logging
import json
import re

from flask import Blueprint, jsonify, request, Response


bp = Blueprint('api', __name__, url_prefix='/api')

_log = logging.getLogger(__name__)


sequence_p = re.compile(r'^[A-Z]+$')


@bp.route('/submit/', methods=['POST'])
def submit():
    """
    Request a prediction for the given sequence.

    :param sequence: the sequence
    :return: a json object, containing the field 'jobid'
    """

    sequence = request.form.get('sequence', None)
    if sequence is None or len(sequence) <= 0 or not sequence_p.match(sequence):
        return jsonify({'error': 'invalid sequence input'}), 400

    from serendip_api.tasks import predict
    result = predict.apply_async((sequence,))

    return jsonify({'jobid': result.task_id})


@bp.route('/status/<jobid>/', methods=['GET'])
def status(jobid):
    """
    Request the status of a job.

    :param jobid: the jobid returned by 'submit'
    :return: Either PENDING, STARTED, SUCCESS, FAILURE, RETRY, or REVOKED.
    """

    from serendip_api.application import celery
    result = celery.AsyncResult(jobid)
    job_status = result.status

    response = {'status': job_status}
    if result.failed():
        response['error'] = str(result.traceback)

    return jsonify(response)


@bp.route('/result/<jobid>/', methods=['GET'])
def result(jobid):
    """
    Request the result of a job, that has status SUCCESS.

    :param jobid: the jobid returned by 'submit'
    :return a json object containing the prediction data
    """

    from serendip_api.application import celery
    result = celery.AsyncResult(jobid)
    data = result.result

    response = {'data': data}

    return jsonify(response)


@bp.route('/yasara_scene/', methods=['POST'])
def yasara_scene():
    """
    Download a yasara scene
    """

    data = request.form.get('serendip_data', None)
    if data is None or len(data) <= 0:
        return jsonify({'error': 'invalid input'}), 400

    data = json.loads(data)

    from serendip_api.tasks import yasara_scene as ys
    try:
        scene_result = ys.apply_async((data,))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # put binary data in html response:
    response = Response(scene_result.get(), mimetype='application/octet-stream')
    response.headers["Content-Disposition"] = "attachment; filename=prediction.sce"

    return response
