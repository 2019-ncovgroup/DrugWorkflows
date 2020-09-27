#!/usr/bin/env python3

import sys
import radical.utils as ru


bcache = sys.argv[1]
data   = open('%s/ligand_dict.py' % bcache).read()

exec(data, globals(), locals())

ru.write_json(d, '%s/ligand_dict.json' % bcache)

