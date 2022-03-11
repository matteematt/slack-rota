#!/usr/bin/env python3

import os
import holidays
import functools
import random
import requests
from datetime import datetime, timedelta

names_list_filename = "names.txt"
rota_filename = "rota.txt"
slack_code_filename = "slack_integration_code.txt"

def file_not_exist_or_empty(filename):
  return not os.path.exists(filename) or os.stat(filename).st_size < 5

# Skip weekends and public holidays
def check_is_rota_day(check_date = datetime.today()):
  uk_holidays = holidays.UK()
  return 0 <= check_date.weekday() <= 4 and not (check_date in uk_holidays)


def read_names_list():
  with open(names_list_filename) as f:
    return f.read().splitlines()

def create_rota_string(names):
  today = datetime.today()
  rota_names = random.sample(names, len(names))
  rota_offset = create_rota_dates_list(len(names))
  rota = zip(rota_offset, rota_names)
  return [f'{(today + timedelta(days=count)).strftime("%d %B")} - <{name}>' for count, name in rota]

def create_rota_dates_list(rota_len : int):
  if rota_len == 0:
    return []
  # This is assuming the script won't be run on the weekend (because of the earlier check)
  rota_dates_offset = [0]
  today = datetime.today()
  while len(rota_dates_offset) < rota_len:
    next_val = rota_dates_offset[-1] + 1
    while not check_is_rota_day(today + timedelta(days=next_val)):
      next_val += 1
    rota_dates_offset.append(next_val)
  return rota_dates_offset


def write_rota_file(rota : list):
  with open(rota_filename, 'w') as f:
    if len(rota) == 0:
      f.write("")
    else:
      rota_string = functools.reduce(lambda a,b: f'{a}\n{b}', rota) + '\n'
      f.writelines(rota_string)
    f.close()

def send_new_rota_to_slack(rota):
  rota_string = functools.reduce(lambda a,b: f'{a}\n{b}', rota) + '\n'
  message = f"New Squad Rota!\n{rota_string}"
  send_slack_message(message)

def get_current_person_from_rota():
  with open(rota_filename) as f:
    lines = f.read().splitlines()
    f.close()
  write_rota_file(lines[1:])
  return lines[0]


def alert_current_person_on_slack(user):
  message = f"{user}\nDon't forget it is your day to complete squad rota activities!"
  send_slack_message(message)

def send_slack_message(message : str):
  slack_code = read_slack_code()
  r = requests.post(f'https://hooks.slack.com/services/{slack_code}', json={'text': message})
  if r.status_code >= 400:
    print("FAIL : Unable to successfully post slack message")

def read_slack_code():
  try:
    return read_slack_code.code
  except AttributeError:
    with open(slack_code_filename) as f:
      read_slack_code.code = f.readline().strip()
    return read_slack_code.code


def main():
  print("Running slack rota script")
  if not check_is_rota_day():
    print("Today is not a day where we require a rota")
    return
  if file_not_exist_or_empty(slack_code_filename):
    print(f'Require slack code set in {slack_code_filename} to be able to run slack webhook')
    return
  if file_not_exist_or_empty(names_list_filename):
    print(f'Require list of names in {names_list_filename} in the script directory')
    return
  if file_not_exist_or_empty(rota_filename):
    names = read_names_list()
    rota = create_rota_string(names)
    write_rota_file(rota)
    send_new_rota_to_slack(rota)
    print(rota)
  current = get_current_person_from_rota()
  print(current)
  alert_current_person_on_slack(current)

if __name__ == "__main__":
  main()

