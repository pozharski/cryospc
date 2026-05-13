headerhelp = \
'''
ZIPIT creates an archive (zip format) from a folder.  
'''

from argparse import ArgumentParser, RawDescriptionHelpFormatter
parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                        description=headerhelp)

parser.add_argument('inpath',
  help="The target (folder) to archive.")
parser.add_argument('outpath',
  help="The archive file to create")
parser.add_argument('--timestamp', action='store_true',
  help='Archive name will have a timestamp.')
parser.add_argument('--dry-run', action='store_true',
  help='Dry run, archive not actually created.')

args = parser.parse_args()

import shutil
dest = args.outpath.strip('.zip')
if args.timestamp:
  import time
  dest += time.strftime("_%Y%m%d%H%M%S")
if args.dry_run:
  import sys, logging
  logroot = logging.getLogger()
  logroot.setLevel(logging.DEBUG)
  loghandler = logging.StreamHandler(sys.stdout)
  loghandler.setLevel(logging.DEBUG)
  logformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  loghandler.setFormatter(logformatter)
  logroot.addHandler(loghandler)
  shutil.make_archive(dest, 'zip', args.inpath, dry_run=True, logger=logroot)
else:
  shutil.make_archive(dest, 'zip', args.inpath)
