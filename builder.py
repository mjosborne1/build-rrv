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
        file.write('ValueSet: RANZCRRadiologyReferral\n')
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


def build_rrv_fshfile(infile, errfile, outdir):
    fsh_lines = []
    dupes = {}  # Change to dictionary for lookup
    error_report = []
    cnt = 0

    df = pd.read_csv(infile, sep='\t', dtype={'Target code': str})

    for index, row in df.iterrows():
        if row['Relationship type code'] == "TARGET_EQUIVALENT" and row["Status"] == "ACCEPTED":
            if row['Target code'] in dupes:
                # Add original record to error report if not already added
                if not any(er['Row #'] == dupes[row['Target code']]['Row #'] for er in error_report):
                    error_report.append(dupes[row['Target code']])
                
                # Add duplicate record to the error report
                error_report.append({
                    'Row #': index,
                    'RRS Id': row['Source code'],
                    'Source display': row['Source display'],
                    'Duplicate target concept': row["Target code"],
                    'FSN': row['Target display']
                })
                print(f'...duplicate code detected: {row["Target code"]}, ignoring')
            else:
                cnt += 1
                fsh_lines.append(f'* $sct#{row["Target code"]}')
                
                # Store in dictionary
                dupes[row['Target code']] = {
                    'Row #': index,
                    'RRS Id': row['Source code'],
                    'Source display': row['Source display'],
                    'Duplicate target concept': row["Target code"],
                    'FSN': row['Target display']
                }

    # Ensure output directory exists
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    outfile = os.path.join(outdir, 'rrv.fsh')

    # Write the FHIR Shorthand lines to the output file
    write_header(outfile)  # Ensure this function is defined elsewhere
    with open(outfile, 'a') as file:
        for line in fsh_lines:
            file.write(line + '\n')

    # Write the error report to a CSV file if there are duplicates
    if error_report:
        error_df = pd.DataFrame(error_report)
        error_df.to_csv(errfile, index=False, quoting=csv.QUOTE_ALL)
        print(f'...error report written to {errfile}')

    print(f'...{cnt} rows written to {outfile}')

def run_main(infile,errfile,outdir):
    build_rrv_fshfile(infile,errfile,outdir)