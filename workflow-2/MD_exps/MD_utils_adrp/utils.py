import os 

def create_md_path(label): 
    """
    create MD simulation path based on its label (int), 
    and automatically update label if path exists. 
    """
    md_path = f'omm_runs_{label}'
    try:
        os.mkdir(md_path)
        return md_path
    except: 
        return create_md_path(label + 1)


def touch_file(file): 
    """
    create an empty file for bookkeeping sake
    """
    with open(file, 'w'): 
        pass
