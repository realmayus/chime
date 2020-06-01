import random
from chime.main import prefix


tips: list = [
    f"Executing  {prefix}play ^  searches for the text of the previous message!",
    "Clicking on \"Now playing\" in the 'current song' embed opens the song's URL!",
    "Stay at home!"
]


def get_tip() -> str:
    return random.choice(tips)
