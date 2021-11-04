import re
import random


random.seed("20211104")


def auto_select(user_in: str):
    choices = re.split("or|还是|或者", user_in)
    rand_num = random.randint(0, len(choices) - 1)
    return choices[rand_num]