def send_help(func_name):
    file = open("text/" + func_name)
    return file.read()