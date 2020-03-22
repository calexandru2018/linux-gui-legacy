import logging
import os

from logging.handlers import RotatingFileHandler
try:
    from protonvpn_cli.constants import CONFIG_DIR
except:
    pass

def get_logger():
    """Create the logger.
    """
    formatter = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s")
    log = logging.getLogger("protonvpn-linux-gui")
    log.setLevel(logging.DEBUG)

    #logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)
    try:
        LOGFILE = os.path.join(CONFIG_DIR, "protonvpn-gui.log")
        file_handler = RotatingFileHandler(LOGFILE, maxBytes=3145728, backupCount=1)
        file_handler.setFormatter(formatter)
        log.addHandler(file_handler)
    except NameError:
        pass
    
    return log

gui_logger = get_logger()