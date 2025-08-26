import logging


def configure_logging():
	LOG_FILE = 'logs/debug.log'
	LOG_LEVEL = logging.DEBUG
	LOG_FORMAT = '%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'

	logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL, format=LOG_FORMAT)

	# Optional: Add handlers for console output as well
	console_handler = logging.StreamHandler()
	console_handler.setLevel(logging.WARNING)  # Or any level you want for console
	console_formatter = logging.Formatter('%(levelname)s - %(message)s')
	console_handler.setFormatter(console_formatter)
	logging.getLogger().addHandler(console_handler)


# You can define more loggers or handlers here if needed
