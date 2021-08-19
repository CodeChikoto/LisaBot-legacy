def send_help(func_name):
    file = open("help/" + func_name)
    return file.read()