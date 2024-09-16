import numpy as np
import pandas as pd
import subprocess
import urllib 
import re
import os, io, csv
import json
from datetime import date, timedelta
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

def get_release_date():
    """
       To create the release date for the RRV ValueSet
       Add one day to the current date and return in a string (YYYY-MM-DD)
    """
    current_date = date.today()
    one_day_later = current_date + timedelta(days=1)
    release_date = one_day_later.strftime("%Y-%m-%d")
    return release_date


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
    release_date = get_release_date()
    with open(outfile, 'w') as file:
        file.write('ValueSet: RANZCRRadiologyProcedures\n')
        file.write('Id: ranzcr-radiology-referral\n')
        file.write('Title: "RANZCR Radiology Referral"\n')
        file.write('Description: "Standard codes for use in requesting radiology tests in Australia, derived from the RANZCR Radiology Referral Set (RRS)."\n')
        file.write('* ^meta.profile[+] = "http://hl7.org/fhir/StructureDefinition/shareablevalueset"\n')
        file.write('* ^url = "https://ranzcr.com/fhir/ValueSet/radiology-referral"\n')
        file.write('* ^version = "1.0.0"\n')
        file.write('* ^extension[http://hl7.org/fhir/StructureDefinition/structuredefinition-fmm].valueInteger = 0\n')
        file.write('* ^status = #draft\n')
        file.write('* ^experimental = false\n')
        file.write(f'* ^date = "{release_date}"\n')
        file.write('* ^publisher = "HL7 Australia"\n')
        file.write('* ^copyright = "This value set includes content from SNOMED CT, which is copyright © 2002+ International Health Terminology Standards Development Organisation (IHTSDO), and distributed by agreement between IHTSDO and HL7. Implementer use of SNOMED CT is not covered by this agreement\nThe SNOMED International IPS Terminology is distributed by International Health Terminology Standards Development Organisation, trading as SNOMED International, and is subject the terms of the [Creative Commons Attribution 4.0 International Public License](https://creativecommons.org/licenses/by/4.0/). For more information, see [SNOMED IPS Terminology](https://www.snomed.org/snomed-ct/Other-SNOMED-products/international-patient-summary-terminology)\n The HL7 International IPS implementation guides incorporate SNOMED CT®, used by permission of the International Health Terminology Standards Development Organisation, trading as SNOMED International. SNOMED CT was originally created by the College of American Pathologists. SNOMED CT is a registered trademark of the International Health Terminology Standards Development Organisation, all rights reserved. Implementers of SNOMED CT should review [usage terms](http://www.snomed.org/snomed-ct/get-snomed-ct) or directly contact SNOMED International: info@snomed.org"')

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