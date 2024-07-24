import unittest
import builder
import os


##infiledefault=os.path.join(homedir,"data","rrs","in","xray-test.tsv")

class TestBuilder(unittest.TestCase):
    def test_get_preferred_term(self):
        """
        Test that get_preferred_term returns the correct SNOMED CT PT for an SCT concept
        """
        homedir=os.environ['HOME']
        infile=os.path.join(homedir,"data","CUREator","in","bacteria_enums.txt")
        outdir=os.path.join(homedir,"data","CUREator","out")
        # Test data
        concepts=[ ("770557001", "Ultrasound guided insertion of peripherally inserted central catheter"),
                ("105377009","This is not a display for Ultrasound of Liver")
              ]
        pt = builder.get_preferred_term(concepts[0][0])
        # Check that we get the correct PT for a code
        self.assertEqual(pt,concepts[0][1])
        # Check that PT does not match the string
        pt = builder.get_preferred_term(concepts[1][0])
        self.assertNotEqual(pt,concepts[1][1])
