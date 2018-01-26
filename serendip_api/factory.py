import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler

from celery import Celery
from flask import Flask

_log = logging.getLogger(__name__)


def create_app(settings=None):
    app = Flask(__name__, static_folder='frontend/static',
                template_folder='frontend/templates')

    app.config.from_object('serendip_api.default_settings')

    # Ignore Flask's built-in logging
    # app.logger is accessed here so Flask tries to create it
    app.logger_name = "nowhere"
    app.logger

    # Use ProxyFix to correct URL's when redirecting.
    from serendip_api.middleware import ReverseProxied
    app.wsgi_app = ReverseProxied(app.wsgi_app)

    # Register blueprints
    from serendip_api.frontend.api.endpoints import bp
    app.register_blueprint(bp)
    from serendip_api.frontend.dashboard.views import bp
    app.register_blueprint(bp)

    return app


def create_celery_app(app):  # pragma: no cover
    app = app or create_app()

    celery = Celery(__name__,
                    backend='amqp',
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    import serendip_api.tasks

    return celery
