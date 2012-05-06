"""Setup a logging helper for our module.


Helpers:
    LOG - out active logger instance
    set_logging_level(level) - adjust the current logging level
"""
import logging
import sys
import time
from collections import namedtuple


# For pretty log messages, if available
try:
    import curses
except ImportError:
    curses = None

LOGLEVEL = "WARNING"

# Logging bits stolen and adapted from:
# http://www.tornadoweb.org/documentation/_modules/tornado/options.html
LogOptions = namedtuple('LogOptions', [
    'loglevel',
    'log_file_prefix',
    'log_file_max_size',
    'log_file_num_backups',
    'log_to_stderr',
])

options = LogOptions(
    loglevel=LOGLEVEL,
    log_file_prefix="",
    log_file_max_size=100 * 1000 * 1000,
    log_file_num_backups=5,
    log_to_stderr=True,
)


def set_logging_level(level):
    """Adjust the current logging level.

    Expect a string of DEBUG, WARNING, INFO, etc.

    """
    logging.getLogger('breadable').setLevel(getattr(logging, level))


def enable_pretty_logging():
    """Turns on formatted logging output as configured.

    This is called automatically by `parse_command_line`.
    """
    root_logger = logging.getLogger()
    if options.log_file_prefix:
        channel = logging.handlers.RotatingFileHandler(
            filename=options.log_file_prefix,
            maxBytes=options.log_file_max_size,
            backupCount=options.log_file_num_backups)
        channel.setFormatter(_LogFormatter(color=False))
        root_logger.addHandler(channel)

    if (options.log_to_stderr or
        (options.log_to_stderr is None and not root_logger.handlers)):
        # Set up color if we are in a tty and curses is installed
        color = False
        if curses and sys.stderr.isatty():
            try:
                curses.setupterm()
                if curses.tigetnum("colors") > 0:
                    color = True
            except Exception:
                pass
        channel = logging.StreamHandler()
        channel.setFormatter(_LogFormatter(color=color))
        root_logger.addHandler(channel)


class _LogFormatter(logging.Formatter):
    def __init__(self, color, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)
        self._color = color
        if color:
            # The curses module has some str/bytes confusion in python3.
            # Most methods return bytes, but only accept strings.
            # The explict calls to unicode() below are harmless in python2,
            # but will do the right conversion in python3.
            fg_color = unicode(curses.tigetstr("setaf") or
                               curses.tigetstr("setf") or "", "ascii")
            self._colors = {
                logging.DEBUG: unicode(
                    curses.tparm(fg_color, curses.COLOR_CYAN),
                   "ascii"),
                logging.INFO: unicode(
                    curses.tparm(fg_color, curses.COLOR_GREEN),
                    "ascii"),
                logging.WARNING: unicode(
                    curses.tparm(fg_color, curses.COLOR_YELLOW),  # Yellow
                    "ascii"),
                logging.ERROR: unicode(
                    curses.tparm(fg_color, curses.COLOR_RED),  # Red
                    "ascii"),
            }
            self._normal = unicode(curses.tigetstr("sgr0"), "ascii")

    def format(self, record):
        try:
            record.message = record.getMessage()
        except Exception, e:
            record.message = "Bad message (%r): %r" % (e, record.__dict__)
        record.asctime = time.strftime(
            "%y%m%d %H:%M:%S", self.converter(record.created))
        prefix = '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d]' % \
            record.__dict__
        if self._color:
            prefix = (self._colors.get(record.levelno, self._normal) +
                      prefix + self._normal)
        formatted = prefix + " " + record.message
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            formatted = formatted.rstrip() + "\n" + record.exc_text
        return formatted.replace("\n", "\n    ")


# Set up log level and pretty console logging by default
logging.getLogger('breadable').setLevel(getattr(logging, LOGLEVEL))
enable_pretty_logging()
LOG = logging.getLogger('breadable')
