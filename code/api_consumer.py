#!/usr/bin/env python3

import re
import sys
import glob
import pytz
import json
import uuid
import argparse
import requests
import pandas as pd
import configparser
from time import sleep
from datetime import date
from datetime import datetime
from operator import itemgetter

def get_sys_args():
  parser = argparse.ArgumentParser(description = 'This program consumes a configured source API')
  parser.add_argument('--source', required = True, help = "the source API's arg code/alias (refer to core.ini for more info)")
  parser.add_argument('--states', default = 'ALL', help = 'a comma-seperated string of states to process (states must be declared in their abbreviated form)')
  parser.add_argument('-m', '--manual', action = 'store_true', default = False, help = "activate to manually input the API's query string")
  return parser.parse_args()

def store_log(log_file_name, log):
  with open(f'../logs/{log_file_name}.json', 'w+') as log_file:
      json.dump(log, log_file, indent = 2)
    
def get_current_zulu_time(strftime):
  return f'{datetime.now(tz = pytz.UTC).strftime(strftime)}Z'

def get_configs(config_name):
  configs = configparser.RawConfigParser()
  configs_path = f'../configs/query_parameters/{config_name}.ini'
  
  if config_name in [re.search('([a-z]+).ini$', config_file).group(1) for config_file in glob.glob("../configs/*.ini")]:
    configs_path = f'../configs/{config_name}.ini'
      
  configs.read(configs_path)
  return configs

def get_current_YYYYmmdd():
  return date.today().strftime('%Y%m%d')

def replace_placeholders(query_string, configs, shim_state, state):
  placeholders = re.findall('([aA-zZ]+)_placeholder', query_string)
  
  for placeholder in placeholders:
    if placeholder == 'state' and shim_state == False:
      query_string = query_string.replace(f'{placeholder}_placeholder', state)
    elif placeholder == 'state' and shim_state == True:
      query_string = query_string.replace(f'{placeholder}_placeholder', configs[state]['state'])
    elif placeholder == 'user' or placeholder == 'password':
      continue
    else:
      query_string = query_string.replace(f'{placeholder}_placeholder', configs['driver' if state == 'ALL' else state][placeholder])      
  return query_string

def unsecured_authentication(api_call, credentials):
  api_call = api_call.replace('user_placeholder', credentials['user'])
  api_call = api_call.replace('password_placeholder', credentials['password'])
  return api_call

def update_based_on_epa_source(update_args):
  update_args['updater_value'] = get_current_YYYYmmdd()
  update_api_configs(update_args)
  
def update_based_on_updater_key_in_headers(update_args):
  df, updater_key = itemgetter('df','updater_key')(update_args)
  df = df.sort_values(by = updater_key, ascending = False)
  updater_key_index = list(df.columns.values).index(updater_key)
  update_args['updater_value'] = df.iloc[0, updater_key_index]
  update_api_configs(update_args)
  
def update_api_configs(update_args):
  source, state, updater_key, updater_value = itemgetter('source', 'state', 'updater_key', 'updater_value')(update_args)
  config_file_name = f'{source}_cluster' if state == 'ALL' else source
  source_api_configs = get_configs(config_file_name)  
  source_api_configs.set('driver' if state == 'ALL' else state, updater_key, updater_value)
  
  with open(f'../configs/query_parameters/{config_file_name}.ini', 'w') as config_file:
    source_api_configs.write(config_file)
    
def get_request_args(prerequest_args):
  core_configs, source, source_configs, query_string, api_configs = itemgetter('core_configs', 'source', 'source_configs', 'query_string', 'api_configs')(prerequest_args)
  state, base, endpoint, strftime, uuid, credentials = itemgetter('state', 'base', 'endpoint', 'strftime', 'uuid', 'credentials')(prerequest_args)
  shim_state = core_configs.has_option(source, 'shim_state')
      
  if core_configs.has_option(source, 'limiter_key'):
    limiter_value = getattr(sys.modules[__name__], source_configs['limiter_method'])()
    query_string = query_string.replace(f"{source_configs['limiter_key']}_placeholder", limiter_value)

  query_string = replace_placeholders(query_string, api_configs, shim_state, state)
  api_call = f'{base}{endpoint}?{query_string}'
  request = {'consumption_time': get_current_zulu_time(strftime)}
  request_args = {
    'api_call': api_call,
    'payload_data': source_configs['payload_data'],
    'request': request,
    'source': source,
    'state': state,
    'updater_key': source_configs['updater_key'],
    'updater_method': source_configs['updater_method'],
    'uuid': uuid
  }
        
  if credentials:
    request_args['credentials'] = credentials
    request_args['authentication_method'] = getattr(sys.modules[__name__], source_configs['authentication_method'])

  return request_args

def handle_request(args):
  api_call, payload_data, request, source, updater_method, uuid = itemgetter('api_call', 'payload_data', 'request', 'source', 'updater_method', 'uuid')(args)
  credentials = None
  authentication_method = None
  
  if 'credentials' in args.keys():
    credentials, authentication_method = itemgetter('credentials', 'authentication_method')(args)
      
  request['api_call'] = api_call
  request['consumption_time']
  
  if credentials:
    api_call = authentication_method(api_call, credentials)
          
  headers = None
  response = None
  request['api_call_status'] = 'Success'

  try:
    response = requests.get(api_call, headers = headers)
  except requests.exceptions.InvalidSchema:
    request['api_call_status'] = 'Fail'
    message = f'Invalid API call detected - {api_call}'
    request['message'] = message
    print(f'\t{message}')
  
  try:
    response.raise_for_status()
  except requests.exceptions.HTTPError as error:
    request['api_call_status'] = 'Fail'
    message = f'{error}'
    request['message'] = message
    print(f'\t{message}')
  except Exception as error:
    request['api_call_status'] = 'Fail'
    request['message'] = f'Encountered the following runtime anamoly - {error.message}'
    print(f'\tEncountered the following runtime anamoly:\n\t{error.message}')
    
  if(request['api_call_status'] == 'Success'):     
    data = response.json()['Data'] if payload_data == 'Data' else response.json()[payload_data]
    csv_file_name = re.sub('\.|:', '-', f"{source}_{request['consumption_time']}")
    df = pd.DataFrame.from_dict(data)
    df.to_csv(f'../output/{csv_file_name}@{uuid}.csv', index = False)
    
    update_args = {
      'df': df,
      'source': source,
      'state': args['state'],
      'updater_key': args['updater_key']
    }
    
    update_api_configs = getattr(sys.modules[__name__], updater_method)
    update_api_configs(update_args)
    print(f'\tConsumed {api_call} successfully')
  return request

def main(log = {}):
  sys_args = get_sys_args()
  core_configs = get_configs('core')
  source = sys_args.source
  source_configs = core_configs[source]
  strftime = core_configs['strftime'][source] if core_configs.has_option('strftime', source) else core_configs['defaults']['strftime']
  
  log['uuid'] = str(uuid.uuid1())
  log['start_time'] = get_current_zulu_time(strftime)
  log_file_name = re.sub('\.|:', '-', f"{source}_{log['start_time']}@{log['uuid']}")
  
  api_configs = get_configs(source)
  states = False if sys_args.states == 'ALL' else sys_args.states.split(',')
  
  if(states):
    for state in states:
      if state not in set(api_configs.sections()):
        log['end_time'] = get_current_zulu_time(strftime)
        log['runtime_status'] = 'Fail'
        log['message'] = 'Invalid state sys args detected'
        log['states'] = states
        store_log(f'{log_file_name}$Fail', log)
        raise SystemExit('This program will not execute unless valid state sys args are provided')
  else:
    states = list(api_configs.sections())

  log['states'] = states
  log['requests'] = []
  base = source_configs['base']
  endpoint = source_configs['endpoint']
  credentials = get_configs('credentials')[source] if get_configs('credentials').has_section(source) else False
    
  prerequest_args = {
      'core_configs': core_configs,
      'source': source,
      'source_configs': source_configs,
      'api_configs': api_configs,
      'base': base,
      'endpoint': endpoint,
      'strftime': strftime,
      'uuid': log['uuid'],
      'credentials': credentials
  }
      
  if(sys_args.manual):
    print('Manual Mode Activated')
    query_string = input('Enter the query string you wish to incorporate into the API call: ')
    state = 'ALL'
    
    try:
      state = re.search('state=(..)', query_string).group(1)
    except AttributeError:
      state_parameter = core_configs.has_option(source, 'state_parameter')
      
      if not state_parameter:
        log['end_time'] = get_current_zulu_time(strftime)
        log['runtime_status'] = 'Fail'
        log['message'] = 'Invalid manual state parameter detected'
        log['manual_query_string'] = query_string
        store_log(f'{log_file_name}$Fail', log)
        raise SystemExit("This program will not execute unless the query string's state parameter is valid")  
    
    api_call = f'{base}{endpoint}?{query_string}'
    print(f'\nProcessing {api_call} for {source}...')
        
    prerequest_args['query_string'] = query_string
    prerequest_args['state'] = state
    request_args = get_request_args(prerequest_args)      
    request = handle_request(request_args)
    print(f'Finished processing {api_call} for {source}')
    log['requests'].append(request)

  elif len(states) == 51 and core_configs.has_option(source, 'state_parameter'):
    print(f'Processing {source} for all states...')
    query_string = core_configs[source]['query_string']
    state_parameter = core_configs[source]['state_parameter']
    affixed_string = re.search(f'{state_parameter}(\s|&)', query_string)
    
    if affixed_string:
      state_parameter = f'{state_parameter}{affixed_string.group(1)}'
          
    prerequest_args['query_string'] = query_string.replace(state_parameter, '')
    prerequest_args['api_configs'] = get_configs(f'{source}_cluster')
    prerequest_args['state'] = 'ALL'
    request_args = get_request_args(prerequest_args)  
    request = handle_request(request_args)
    print(f'Finished processing {source} for all states')
    log['requests'].append(request)

  else:
    last_state_index = len(states) - 1
    
    for index, state in enumerate(states):
      print(f'Processing {source} for {state}...')
      prerequest_args['query_string'] = core_configs[source]['query_string']
      prerequest_args['state'] = state
      request_args = get_request_args(prerequest_args)
      request = handle_request(request_args)
      log['requests'].append(request)
      
      seconds_between_api_calls = int(core_configs['defaults']['seconds_between_api_calls'])
      
      if index != last_state_index:
        print(f'Finished processing {source} for {state}, please wait {seconds_between_api_calls} seconds before the next call as a courtesy to the server...\n')
        sleep(seconds_between_api_calls)
      else:
        print(f'Finished processing {source} for {state}')

  log['end_time'] = get_current_zulu_time(strftime)
  log['runtime_status'] = log['requests'][0]['api_call_status'] if len(log['requests']) == 1 else 'Success'
  
  store_log(log_file_name if log['runtime_status'] == 'Success' else f'{log_file_name}$Fail', log)
  
  
if __name__ == '__main__':
  main()