import logging
import sys

LEVEL_COLORS = {
    "DEBUG": "\033[36m",     # cyan
    "INFO": "\033[32m",      # green
    "WARNING": "\033[33m",   # yellow
    "ERROR": "\033[31m",     # red
    "CRITICAL": "\033[35m",  # magenta
}
RESET = "\033[0m"


class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = LEVEL_COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{RESET}"
        return super().format(record)


def setup_logging(level: str = "INFO") -> None:
    fmt = "%(levelname)s:     [%(asctime)s] - %(message)s"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S"))

    logging.basicConfig(level=level, handlers=[handler], force=True)

    for noisy in ("httpx", "httpcore", "openai", "langchain", "langgraph"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
