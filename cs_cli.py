import os

def get_cli():
  try:
    from cryosparc_compute import client
  except:
    print('Failed to import cryosparc_compute module...')
    return None 
  cshost = os.environ.get('CRYOSPARC_MASTER_HOSTNAME')
  csport = os.environ.get('CRYOSPARC_COMMAND_CORE_PORT')
  if cshost and csport:
    return client.CommandClient(host=os.environ['CRYOSPARC_MASTER_HOSTNAME'], port=int(os.environ['CRYOSPARC_COMMAND_CORE_PORT']))
  print("Access to CryoSPARC not configured...")
  return None
