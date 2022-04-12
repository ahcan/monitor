import json
import logging
import logging.config
import logging.handlers

from .first_check import FirstCheck
from .last_check import LastCheck
from .video_check import VideoCheck
from .required_check import RequiredCheck
from .as_required_check import AsRequiredCheck
from .monitor import Monitor
from .snmp_agent import Snmp, AgentSnmp
from pathlib import Path
currentPath = Path().parent.absolute()

with open("{0}/config/python_logging_configuration.json".format(currentPath), 'r') as configuration_file:
    config_dict = json.load(configuration_file)
logging.config.dictConfig(config_dict)
# Create the Logger
logger = logging.getLogger(__name__)

