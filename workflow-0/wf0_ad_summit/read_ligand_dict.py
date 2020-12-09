#!/usr/bin/env python3

import radical.utils as ru


data = open('./ligand_dict.py').read()

exec(data, globals(), locals())

ru.write_json(d, './ligand_dict.json')

