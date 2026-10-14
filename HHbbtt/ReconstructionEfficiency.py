import matplotlib.pyplot as plt
import mplhep as hep
plt.style.use(hep.style.CMS)

from Utils import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Arguments for ReconstructionEfficiency.py')
    parser.add_argument('--max-files', type=int, default=None, help='Maximum number of files to process.')
    parser.add_argument('--skip-merging', action='store_true', required=False, help='Skip merging of NGT and HLT input files.')
    parser.add_argument('--skip-histos', action='store_true', required=False, help='Skip histogram creation.')
    parser.add_argument('--histo-dir', default='Dataframes', help='Output directory for the merged dataframe and histograms.')
    parser.add_argument('--plots-dir', default='Plots_RecoEff', help='Output directory for the plots.')
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    histo_dir = script_dir + "/" + args.histo_dir
    os.makedirs(histo_dir, exist_ok=True)
    print(f"[INFO] Output directory for the merged dataframe and histograms: {histo_dir}")

    ##############################################################
    # Prepare the merged dataframe from NGT and HLT input files
    ##############################################################

    path_df = f"{histo_dir}/df_ngt_hlt.root"

    if not args.skip_merging:

        base_dir_hlt = "/data/evernazz/NanoAOD/SummerStudent/2026_10_08/CMSSW_17_0_0_pre6/src/AAA_Test/OldProduction/HLTMenu_ParT/"
        base_dir_ngt = "/data/evernazz/NanoAOD/SummerStudent/2026_10_08/CMSSW_17_0_0_pre6/src/AAA_Test/OldProduction/NGTScoutingFullTracking/"
        df = merge_hlt_ngt(base_dir_hlt, base_dir_ngt, path_df, args)

    else:

        df = ROOT.RDataFrame("Events", path_df)

    # # DEBUG
    # print("Available branches: ")
    # for branch in df.GetColumnNames():
    #     print(branch)

    if not args.skip_histos:

        ##############################################################
        # Define gen-level variables for the analysis
        ##############################################################

        df = FindHHGenObjects(df)

        # df = df.Define("has_two_bjets", "(bjet1_idx != -1) && (bjet2_idx != -1) && (bjet1_idx != bjet2_idx)")
        # print(f"[INFO] Total entries after filtering for events with two b-jets (pT > 10 GeV): {df.Filter("has_two_bjets").Count().GetValue()}")

        # Acceptance of NGT Scouting
        df = df.Define("pass_NGT", "DST_NGTScouting")

        ##############################################################
        # Define channels
        ##############################################################

        df = FindHHChannels(df)

        collection_dict = {
            "hlt" : {
                "ele": "hltElectron",
                "muon": "hltMuon",
                "tau": "hltHpsPFTau", # "hltAK4PuppiJet"
                "tauTag": "hltHpsPFTau_deepTauVSjet", # "hltAK4PuppiJet_UParT_prob_b"
                "bjet": "hltAK4PuppiJet",
                "bjetTag": "hltAK4PuppiJet_DeepFlavour_prob_b",
            },
            "l1" : {
                "ele": "L1GTtkElectron",
                "muon": "L1GTgmtTkMuon",
                "tau": "L1nnPuppiTau",
                "tauTag": "L1nnPuppiTau_id",
                "bjet": "L1puppiJetSC4NG",
                "bjetTag": "L1puppiJetSC4NG_bTagScore",
            }
        }

        # ETAU
        df_etau = df.Filter("ch_etau")
        df_etau = FindGenFinalState(df_etau, "etau")
        df_etau = FindRecoMataching(df_etau, "etau", collection_dict)

        # MUTAU
        df_mutau = df.Filter("ch_mutau")
        df_mutau = FindGenFinalState(df_mutau, "mutau")
        df_mutau = FindRecoMataching(df_mutau, "mutau", collection_dict)
        
        # TAUTAU
        df_tautau = df.Filter("ch_tautau")
        df_tautau = FindGenFinalState(df_tautau, "tautau")
        df_tautau = FindRecoMataching(df_tautau, "tautau", collection_dict)
        

