
import os
import logging
from typing import List

try:
    from foglamp.common import logger
    _logger = logger.setup(__name__, level=logging.INFO)
except:
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

__author__ = "Mohit Rajput"
__copyright__ = "Copyright (c) 2025 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


def query_syslog(
    match: str = "", severity: str = "", limit: int = 5
) -> List[str]:
    """Query the system log (/var/log/syslog) using substring, severity, and line limit.

    Args:
        match (str): Substring to match in the log line (case-insensitive). Example: "failed".
        severity (str): Filter by syslog severity (e.g., INFO, WARNING, ERROR, CRITICAL).
        limit (int): Maximum number of matched lines to return.

    Returns:
        List[str]: A list of syslog lines that match the criteria. If the returned
                   list is empty it means nothing has been detected that matches
                   the filter.
    """
    logfile = "/var/log/syslog"
    results = []

    severity = severity.upper()
    match = match.lower()

    if not os.path.exists(logfile):
        _msg = f"Syslog file not found: {logfile}"
        _logger.warning(_msg)
        return _msg

    try:
        with open(logfile, "r") as f:
            for line in reversed(f.readlines()):
                line_lc = line.lower()

                # Apply match and severity filters
                if match and match not in line_lc:
                    continue
                if severity and severity not in line.upper():
                    continue

                results.append(line.strip())

                if limit is not None:
                    if len(results) >= limit:
                        break
    except Exception as e:
        _msg = f"Error reading syslog: {str(e)}"
        _logger.error(_msg)
        return [_msg]

    _logger.debug(f"Total syslog entries which matches the filter: {len(results)}.")

    return results
