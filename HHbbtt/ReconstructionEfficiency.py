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
    parser.add_argument('--tau-reco', type=str, choices=['DeepTau', 'ParT'], default='DeepTau', help='Tau reconstruction strateggy (default: %(default)s).')
    args = parser.parse_args()

    tau_reco = args.tau_reco
    script_dir = os.path.dirname(os.path.abspath(__file__))
    histo_dir = script_dir + "/" + args.histo_dir
    os.makedirs(histo_dir, exist_ok=True)
    print(f"[INFO] Output directory for the merged dataframe and histograms: {histo_dir}")

    ##############################################################
    # Prepare the merged dataframe from NGT and HLT input files
    ##############################################################

    path_df = f"{histo_dir}/df_ngt_hlt_{tau_reco}.root"

    if not args.skip_merging:

        base_dir_hlt = "/data/evernazz/NanoAOD/SummerStudent/2026_10_08/CMSSW_17_0_0_pre6/src/AAA_Test/TriggerStudies/HHbbtt/LaunchReprocessing/DeepTau/HLTMenu"
        base_dir_ngt_DeepTau = "/data/evernazz/NanoAOD/SummerStudent/2026_10_08/CMSSW_17_0_0_pre6/src/AAA_Test/TriggerStudies/HHbbtt/LaunchReprocessing/DeepTau/NGTMenu"
        base_dir_ngt_ParT = "/data/evernazz/NanoAOD/SummerStudent/2026_10_08/CMSSW_17_0_0_pre6/src/AAA_Test/TriggerStudies/HHbbtt/LaunchReprocessing/ParT/NGTMenu"
        base_dir_ngt = base_dir_ngt_DeepTau if tau_reco == "DeepTau" else base_dir_ngt_ParT
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

        # Acceptance of NGT Scouting
        df = df.Define("pass_NGT", "DST_PFScouting")

        ##############################################################
        # Define channels
        ##############################################################

        df = FindHHChannels(df)

        collection_dict = {
            "hlt" : {
                "ele": "hltElectron",
                "muon": "hltMuon",
                "tau": "hltHpsPFTau" if tau_reco == "DeepTau" else "hltAK4PuppiJet",
                "tauTag": "hltHpsPFTau_deepTauVSjet" if tau_reco == "DeepTau" else "hltAK4PuppiJet_ParT_TauvsAll",
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

        # DEBUG
        print(f"[INFO] Events in etau channel: {df_etau.Count().GetValue()}")
        df_etau = df_etau.Define("has_2genbjets", "(bjet1_idx != -1) && (bjet2_idx != -1) && (bjet1_idx != bjet2_idx)")
        print(f"[INFO] Events with two gen b-jets (pT > 10 GeV): {df_etau.Filter("has_2genbjets").Count().GetValue()}")
        df_etau = df_etau.Define("has_2hltbjets", "(hlt_bjet1_idx != -1) && (hlt_bjet2_idx != -1)")
        print(f"[INFO] Events with two b-jets: {df_etau.Filter("has_2hltbjets").Count().GetValue()}")
        df_etau = df_etau.Define("has_hltele", "(hlt_ele_idx != -1)")
        print(f"[INFO] Events with one electron: {df_etau.Filter("has_hltele").Count().GetValue()}")
        df_etau = df_etau.Define("has_hlttau", "(hlt_tau_idx != -1)")
        print(f"[INFO] Events with one tau: {df_etau.Filter("has_hlttau").Count().GetValue()}")
        print(f"[INFO] Events with two b-jets, one electron, one tau: {df_etau.Filter("has_2hltbjets && hlt_ele_idx && hlt_tau_idx").Count().GetValue()}")
        
        # MUTAU
        df_mutau = df.Filter("ch_mutau")
        df_mutau = FindGenFinalState(df_mutau, "mutau")
        df_mutau = FindRecoMataching(df_mutau, "mutau", collection_dict)
        
        # TAUTAU
        df_tautau = df.Filter("ch_tautau")
        df_tautau = FindGenFinalState(df_tautau, "tautau")
        df_tautau = FindRecoMataching(df_tautau, "tautau", collection_dict)
        

