#!/usr/bin/env python3

import sys
import radical.utils as ru

bcache = sys.argv[1]

exec(open('%s/ligand_dict.py' % bcache, globals(), locals())
ru.write_json(d, '%s/ligand_dict.json', bcache)

