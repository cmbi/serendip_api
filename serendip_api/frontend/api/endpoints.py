import logging

from flask import Blueprint, jsonify, request, Response


bp = Blueprint('api', __name__, url_prefix='/api')

_log = logging.getLogger(__name__)


@bp.route('/submit/', methods=['POST'])
def submit():
    """
    Request a prediction for the given sequence.

    :param sequence: the sequence
    :return: a json object, containing the field 'jobid'
    """

    sequence = request.form.get('sequence', None)
    if sequence is None or len(sequence) <= 0:
        return jsonify({'error': 'invalid input'}), 400

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
        response['message'] = str(result.traceback)

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
