import dotenv
from os import environ as env
dotenv.load_dotenv()

SUDO_PSW = env.get("SUDO_PSW")
assert SUDO_PSW is not None, "SUDO_PSWD is not set in .env file"

APP_PATH = env.get("APP_PATH")
assert APP_PATH is not None, "NC_PATH is not set in .env file"
