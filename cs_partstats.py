#!/usr/bin/env python3

from argparse import ArgumentParser, RawDescriptionHelpFormatter

headerhelp = \
'''
The script aims to provide various statistical parameters on particle
stacks in cryosparc.  It's under development, so new features will be
added and it will never be a final product.  At the moment, it prints
out the range of defocus values observed in a stack.
---
Help? Gondor needs no help! // Boromir, son of Denethor (apocryphal)
'''

import os
import numpy as np

def process_metadata(args):
  if args.cspath:
    cspath = args.cspath
  else:
    cli = get_cli(args)
    if cli is None:
      return
    jobdata = cli.get_job(args.pid, args.jobid)
    print(jobdata['job_type'])
    if jobdata['job_type'] == 'nonuniform_refine_new':
      cspath = cli.get_result_download_abs_path(args.pid, args.jobid+'.particles.ctf')
    else:
      print("Unlisted job type ", jobdata['job_type'])
      return
  if os.path.exists(cspath):
    print('Metadata file found at '+cspath)
  else:
    print("Metadata file NOT found at "+cspath)
    return
  particle_data = np.load(cspath)
  print('Metadata availabale for ',len(particle_data), ' particles')
  d=np.sqrt((particle_data['ctf/df1_A']**2+particle_data['ctf/df2_A']))/10000
  d.sort()
  print("Defocus range: %.3f <-> %.3f (min to max), %.3f <-> %.3f (95%% all particles)" % (d[0],d[-1],d[int(d.shape[0]*0.025)],d[int(d.shape[0]*0.975)]))
  if args.show_plot:
    from matplotlib import pyplot as plt
    plt.hist(d,100,density=True)
    plt.ylabel('Shift Y')
    plt.xlabel('Defocus, \u03bcm')
    plt.show()

def main():
  parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter, description=headerhelp)
  # parser.add_argument('-m', '--mdoc-folder', help='MDOC folder')
  parser.add_argument('-p', '--pid', help='Project ID')
  parser.add_argument('-j', '--jobid', help='Exposure export job ID')
  parser.add_argument('-i', '--cspath', help='Path to cryoSPARC numpy metadata file')
  # parser.add_argument('-o', '--output-npy', help='Output numpy data file')
  # parser.add_argument('-n', '--input-npy', help='Intput numpy data file')
  parser.add_argument('--show-plot', action='store_true', help='Plot the 2D shift distribution')
  # parser.add_argument('--dry-run', action='store_true', help='Dry run, cryoSPARC metadata file will not be updated.')
  args = parser.parse_args()

  # if args.mdoc_folder is not None:
  #   data = parse_mdocs(args)
  # elif args.input_npy is not None:
  #   data = parse_npy(args)

  process_metadata(args)
  
if __name__ == "__main__":
    main()
 

