from imp import reload

import hmc.hmmmAssembler
import hmc.hmmmSimulator

def assemble(file_name, output_name):
    reload(hmc.hmmmAssembler)
    return hmc.hmmmAssembler.main(file_name, output_name)

def run(file_name, debug=None):
    reload(hmc.hmmmSimulator)

    if debug is True:
        hmc.hmmmSimulator.main(['-f', file_name, '--debug'])
    elif debug is False:
        hmc.hmmmSimulator.main(['-f', file_name, '--no-debug'])
    else:
        hmc.hmmmSimulator.main(['-f', file_name])
