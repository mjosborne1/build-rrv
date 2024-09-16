import argparse
import os
import builder

homedir=os.environ['HOME']
parser = argparse.ArgumentParser()
infiledefault=os.path.join(homedir,"data","rrv-fsh","in","RRS_Candidates_4.4.tsv")
outdirdefault=os.path.join(homedir,"data","rrv-fsh","out")
parser.add_argument("-i", "--infile", help="S2S File from Export", default=infiledefault)
parser.add_argument("-o", "--outdir", help="output dir for FHIR artefacts", default=outdirdefault)
args = parser.parse_args()
print("Started")
builder.run_main(args.infile,args.outdir)
print("Finished")