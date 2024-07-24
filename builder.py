import numpy as np
import pandas as pd
import subprocess
import urllib 
import re
import os, io, csv
import json
from fhirpathpy import evaluate

baseurl="https://r4.ontoserver.csiro.au/fhir"
system="http://snomed.info/sct"

def path_exists(path):
    if os.path.exists(path):
        return True
    else:
        print("Warning: "+path+" does not exist, creating path.")
        os.makedirs(path, exist_ok=True)
        if os.path.exists(path):
           return True
        else:
           return False


def get_preferred_term(code):
    cslookup='/CodeSystem/$lookup'  
    query=baseurl+cslookup+'?system='+urllib.parse.quote(system,safe='')+"&code="+code+"&property=display"
    command = ['curl', '-H "Accept: application/fhir+json" ' , '--location', query]
    result = subprocess.run(command, capture_output=True)
    data =  json.loads(result.stdout)
    concepts = evaluate(data,"parameter.where(name = \'display\').valueString")
    pt = concepts[0]
    return pt


def write_header(outfile):
    with open(outfile, 'w') as file:
        file.write('ValueSet: RANZCRRadiologyReferral\n')
        file.write('Id: ranzcr-radiology-referral\n')
        file.write('Title: "RANZCR Referral Procedures"\n')
        file.write('Description: "Standard codes for use in requesting radiology tests in Australia, derived from the RANZCR Radiology Referral Set (RRS)."\n')
        file.write('* ^meta.profile[+] = "http://hl7.org/fhir/StructureDefinition/shareablevalueset"\n')
        file.write('* ^url = "https://ranzcr.com/fhir/ValueSet/radiology-referral"\n')
        file.write('* ^version = "1.0.0"\n')
        file.write('* ^extension[http://hl7.org/fhir/StructureDefinition/structuredefinition-fmm].valueInteger = 0\n')
        file.write('* ^status = #draft\n')
        file.write('* ^experimental = false\n')
        file.write('* ^date = "2024-07-17"\n')
        file.write('* ^publisher = "HL7 Australia"\n')


def build_rrv_fshfile(infile,outdir):
    fsh_lines = []
    dupes = []
    cnt=0
    df = pd.read_csv(infile, sep='\t', dtype={'Target code':str})
    for index,row in df.iterrows():
        # Format the FHIR Shorthand line
        if row['Relationship type code'] == "TARGET_EQUIVALENT":
           # display = get_preferred_term(row['Target code'])
            if row['Target code'] in dupes:
                print(f'...duplicate code detected: {row['Target code']}, ignoring')
                continue
            else:
                cnt+=1
                #fsh_lines.append(f'* $sct#{row['Target code']} "{display}"')
                fsh_lines.append(f'* $sct#{row['Target code']}')
            dupes.append(row['Target code'])

    if path_exists(outdir):
        outfile =  os.path.join(outdir,f'rrv.fsh')

    # Write the FHIR Shorthand lines to the output file
    write_header(outfile)
    with open(outfile, 'a') as file:
        for line in fsh_lines:
            file.write(line + '\n')
    
    # End 
    print(f'...{cnt} rows written to {outfile}')

def run_main(infile,outdir):
    build_rrv_fshfile(infile,outdir)