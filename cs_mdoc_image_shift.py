#!/usr/bin/env python3

from argparse import ArgumentParser, RawDescriptionHelpFormatter

headerhelp = \
'''
Adds image shifts to CryoSPARC micrograph metadata.  For this to work,
you have to have permissions to modify cryoSPARC metadata files in 
place.  You can provide explicit path to the cryoSPARC metadata file
(look under Outputs tab) or provide the project ID (e.g. P304) and
job ID (e.g. J297) and script will locate the path - however,
this likely requires that you run the script as cryosparc master
user that has access to cryosparc_compute module (which can be
activate by executing "eval $(cryosparcm env)").

Currently, only "Live exposure export" and 
                "Manually curate exposures" (v2)
job types are recognized and will be properly processed.  Ask
the man to add some other job type (still, it should be the one
that carries the mscope_params metadata and original 
movie_blob/path field).

You can try other metadata files as well, but it will only
work on files that list original micrograph file names - i.e. the 
movie_blob/path field must be present.  Try it at your own risk.

Standard use of this script is to pull the image shift data from
SerialEM data collection session to use it subsequently to cluster
micrographs for the CTF refinement (see Exposure group utilities 
job in cryoSPARC for details).  The man recommends to use k-means
clustering algorithm.  Do not forget to check the box to split the 
particles into sets.  Also, most of the time you won't know how many
inage shift groups will be needed, so run the job with the default 
number, inspect the image shift chart and re-run it with the updated
value.

---
Help? Gondor needs no help! // Boromir, son of Denethor (apocryphal)
'''

import re, os
import numpy as np

from cs_cli import get_cli

# def get_cli(args):
#   if args.pid is None:
#     print('Project ID unknown, skipping metadata update...')
#     return None
#   if args.jobid is None:
#     print('Job ID unknown, skipping metadata update...')
#     return None
#   try:
#     from cryosparc_compute import client
#   except:
#     print('Failed to import cryosparc_compute module, skipping metadata update...')
#     return None 
#   cshost = os.environ.get('CRYOSPARC_MASTER_HOSTNAME')
#   csport = os.environ.get('CRYOSPARC_COMMAND_CORE_PORT')
#   if cshost and csport:
#     return client.CommandClient(host=os.environ['CRYOSPARC_MASTER_HOSTNAME'], port=int(os.environ['CRYOSPARC_COMMAND_CORE_PORT']))
#   print("Access to CryoSPARC not configured, skipping metadata update...")
#   return None

def update_metadata(data, args):
  if args.cspath:
    cspath = args.cspath
  else:
    if args.pid is None:
      print('Project ID unknown, skipping metadata update...')
      return None
    if args.jobid is None:
      print('Job ID unknown, skipping metadata update...')
      return None
      cli = get_cli(args)
    if cli is None:
      return
    jobdata = cli.get_job(args.pid, args.jobid)
    if jobdata['job_type'] == 'curate_exposures_v2':
      cspath = cli.get_result_download_abs_path(args.pid, args.jobid+'.exposures_accepted.mscope_params')
    elif jobdata['job_type'] == 'export_live_exposures':
      cspath = cli.get_result_download_abs_path(args.pid, args.jobid+'.accepted_exposures.mscope_params')
    else:
      print("Unlisted job type ", jobdata['job_type'])
      return
  if os.path.exists(cspath):
    print('Metadata file found at '+cspath)
  else:
    print("Metadata file NOT found at "+cspath)
    return
  exposure_data = np.load(cspath)
  print('Metadata availabale for ',len(exposure_data), ' micrographs')
  print('Metadata lists ',sum(exposure_data['mscope_params/beam_shift_known']),' known image shift values' )
  for row in exposure_data:
    fname = os.path.basename(row['movie_blob/path']).decode()
    first_bit = fname.split('_')[0]
    if str(row['uid']).rjust(len(first_bit),'0') == first_bit:
      fname = '_'.join(fname.split('_')[1:])
    datum = data.get(fname, False)
    if datum:
      row['mscope_params/beam_shift'] = datum
      row['mscope_params/beam_shift_known'] = 1
  print('Updated version lists ',sum(exposure_data['mscope_params/beam_shift_known']),' image shift values' )
  if args.dry_run:
    print('Dry run, metadata update skipped.')
  else:
    print('Updating metadata... ', end='')
    with open(cspath,'wb') as fout:
      np.save(fout, exposure_data)
    print('done')

def parse_mdocs(args):
  data, shiftx, shifty = {}, [], []

  ptrn = re.compile(r"ImageShift = (-*\d*\.\d*)\s*(-*\d*\.\d*)")
  fnames = [t for t in os.listdir(args.mdoc_folder) if os.path.splitext(t)[-1]=='.mdoc']
  Nmdoc = len(fnames)
  print("Found ",Nmdoc," mdoc files, processing...")
  for (i,fname) in enumerate(fnames):
    print('(',i+1,' of ',Nmdoc,') ',fname, end='\r')
    with open(os.path.join(args.mdoc_folder,fname)) as f:
      mm = [ptrn.match(t) for t in f.readlines()]
      mm = [[float(x) for x in t.groups()] for t in mm if t]
      if len(mm) == 1:
        data[os.path.splitext(fname)[0]] = mm[0]
        shiftx.append(mm[0][0])
        shifty.append(mm[0][1])
  if args.output_npy:
    max_filename_length = max([len(t) for t in data.keys()])
    outarray = np.fromiter(data.items(), 
                           dtype=[('movie_blob/filename', 'S'+str(max_filename_length)), ('mscope_params/beam_shift', '<f4', (2,))],
                           count = len(data))
    with open(args.output_npy,'wb') as fout:
      np.save(fout, outarray)
    if args.show_plot:
      from matplotlib import pyplot as plt
      plt.plot(shiftx,shifty,'r.')
      plt.ylabel('Shift Y')
      plt.xlabel('Shift X')
      plt.show()
  return data

def handle_the_rest(args, data, shiftx, shifty):
  if args.output_npy:
    max_filename_length = max([len(t) for t in data.keys()])
    outarray = np.fromiter(data.items(), 
                           dtype=[('movie_blob/filename', 'S'+str(max_filename_length)), ('mscope_params/beam_shift', '<f4', (2,))],
                           count = len(data))
    with open(args.output_npy,'wb') as fout:
      np.save(fout, outarray)
  if args.show_plot:
    try:
      from matplotlib import pyplot as plt
      plt.plot(shiftx,shifty,'r.')
      plt.ylabel('Shift Y')
      plt.xlabel('Shift X')
      plt.show()
    except ModuleNotFoundError:
      print("Matplotlib not found in the environment")
  return data  

def parse_npy(args):
  data, shiftx, shifty = {}, [], []
  input_data = np.load(args.input_npy)
  for row in input_data:
    data[row[0].decode()] = row[1].tolist()
    shiftx.append(row[1][0])
    shifty.append(row[1][1])
  handle_the_rest(args, data, shiftx, shifty)
  return data

def main():
  parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter, description=headerhelp)
  parser.add_argument('-m', '--mdoc-folder', help='MDOC folder')
  parser.add_argument('-p', '--pid', help='Project ID')
  parser.add_argument('-j', '--jobid', help='Exposure export job ID')
  parser.add_argument('-i', '--cspath', help='Path to cryoSPARC numpy metadata file')
  parser.add_argument('-o', '--output-npy', help='Output numpy data file')
  parser.add_argument('-n', '--input-npy', help='Intput numpy data file')
  parser.add_argument('--show-plot', action='store_true', help='Plot the 2D shift distribution')
  parser.add_argument('--dry-run', action='store_true', help='Dry run, cryoSPARC metadata file will not be updated.')
  args = parser.parse_args()

  if args.mdoc_folder is not None:
    data = parse_mdocs(args)
  elif args.input_npy is not None:
    data = parse_npy(args)

  update_metadata(data, args)
  
if __name__ == "__main__":
    main()
 

