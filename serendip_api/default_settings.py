from kombu import Exchange, Queue

# Celery
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
CELERY_BROKER_URL = 'amqp://guest@serendipapi_rabbitmq_1'
CELERY_DEFAULT_QUEUE = 'serendip'
CELERY_QUEUES = ( 
    Queue('serendip', Exchange('serendip'), routing_key='serendip'),
)
CELERY_RESULT_BACKEND = 'redis://serendipapi_redis_1/0'
CELERY_TRACK_STARTED = True

# Flask
PROPAGATE_EXCEPTIONS = True

NETSURF_EXE = "/deps/serendip/sequence/netsurfp"
NR70_DB = "/deps/serendip/sequence/nr70_db/nr70"
FASTACMD_EXE = "/deps/blast/bin/fastacmd"
MUSCLE_EXE = "/deps/serendip/muscle"
DYNAMINE_EXE = "/deps/serendip/sequence/DynaMine/dynamine"
RSCRIPT_EXE = "/usr/local/bin/Rscript"
RF_SCRIPT = "/deps/serendip/sequence/server_data_transformation.R"
SERENDIP_DIR = "/deps/serendip"
RESULTS_DIR = "/data/results"

YASARA_SEQUENCE_MACRO = "/usr/src/app/serendip_api/macros/protein_sequence.mcr"
YASARA_SCENE_MACRO = "/usr/src/app/serendip_api/macros/protein_scene.mcr"

POLL_INTERVAL = 10  # seconds
BLAST_TIMEOUT = 10800  # three hours
SOAP_TIMEOUT = 90  # seconds
MRS_BLAST_URL = "http://mrs.cmbi.umcn.nl/mrsws/blast/wsdl"
YASARA_URL = "http://chelonium.cmbi.umcn.nl:7000/api"
