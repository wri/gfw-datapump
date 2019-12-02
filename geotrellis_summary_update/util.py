import datetime


def get_curr_date_dir_name():
    today = datetime.datetime.today()
    return "{}{}{}".format(today.year, today.month, today.day)