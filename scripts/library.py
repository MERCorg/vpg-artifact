from io import StringIO
import subprocess
import time
import logging
import sys

def run_program(cmds, logger, process=None):
    """Runs the given program with sensible defaults, and logs the results to the logger.
    Returns the execution time in seconds."""

    start_time = time.time()

    with subprocess.Popen(
        cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    ) as proc:
        if proc.stdout is not None:
            for line in proc.stdout:
                logger.info(line.strip())

                if process is not None:
                    process(line.strip())

        proc.wait()

        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, proc.args)

    elapsed_time = time.time() - start_time
    return elapsed_time

formatter = logging.Formatter("%(threadName)-11s %(asctime)s %(levelname)s %(message)s")
logging.basicConfig(level=logging.DEBUG)

class MyLogger(logging.Logger):
    """My own logger that stores the log messages into a string stream"""

    def __init__(self, name: str, filename: str | None = None, terminator="\n"):
        """Create a new logger instance with the given name"""
        logging.Logger.__init__(self, name, logging.DEBUG)

        self.stream = StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.terminator = terminator
        handler.setFormatter(formatter)

        if filename is not None:
            self.addHandler(logging.FileHandler(filename))

        standard_output = logging.StreamHandler(sys.stderr)
        standard_output.terminator = terminator

        self.addHandler(handler)
        self.addHandler(standard_output)

    def getvalue(self) -> str:
        """Returns the str that has been logged to this logger"""
        return self.stream.getvalue()