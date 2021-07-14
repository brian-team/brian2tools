import argparse
import os, sys
from brian2tools.nmlimport.nml import NMLMorphology
import logging

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--mute", help="mute morphology info",
                        action="store_true")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-f", "--file",nargs='+',
                    help="file location",dest="file")
group.add_argument("-d", "--directory",
                    help="directory path",dest="dir")
parser.add_argument("--debug",help="set log level to debug",action="store_true")
args = parser.parse_args()

formatter=logging.Formatter('%(name)s - %(levelname)s - %(message)s')
filhandler=logging.FileHandler("{0}/nml.log".format(os.path.dirname(os.path.abspath(
            __file__))),mode='w')
filhandler.setLevel(logging.INFO)
filhandler.setFormatter(formatter)
logger=logging.getLogger(__name__)
logger.addHandler(filhandler)

def populate():
    if args.file:
        return [os.path.join(os.getcwd(), f) for f in args.file]
    elif args.dir:
        dir=os.path.join(os.getcwd(), args.dir)
        return [os.path.join(dir, f) for f in os.listdir(dir) if os.path.isfile(os.path.join(
            dir, f)) and f.endswith('.nml')]

def test_nml(f):
    morph=NMLMorphology(f).morphology
    if not args.mute:
        if morph is None:
            logger.info("No morphology information in this file!!\n\n")
            return
        logger.info("Morphology info:")
        logger.info("distance: {0}".format(morph.distance))
        logger.info("length: {0}".format(morph.length))
        logger.info("coordinates: {0}".format(morph.coordinates))
        logger.info("area: {0}\n\n".format(morph.area))

def nml_reader():
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    files=populate()
    for f in files:
        try:
            logger.info("Reading file {0}".format(f))
            test_nml(f)
        except Exception as e:
            logger.error("Error occured in file {0} \n error: {1}".format(f,e))



if __name__ == '__main__':
    nml_reader()
