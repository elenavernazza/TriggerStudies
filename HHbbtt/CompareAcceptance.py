import matplotlib.pyplot as plt
import mplhep as hep
plt.style.use(hep.style.CMS)

from Utils import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Arguments for CompareAcceptance.py')
    parser.add_argument('--max-files', type=int, default=None, help='Maximum number of files to process.')
    parser.add_argument('--skip-merging', action='store_true', required=False, help='Skip merging of NGT and HLT input files.')
    parser.add_argument('--skip-histos', action='store_true', required=False, help='Skip histogram creation.')
    parser.add_argument('--histo-dir', default='Dataframes', help='Output directory for the merged dataframe and histograms.')
    parser.add_argument('--plots-dir', default='Plots_Acceptance', help='Output directory for the plots.')
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

        # # DEBUG
        # df.Display(["b1_eta", "b1_phi", "b1_pt", "bjet1_idx", "bjet1_partFlav"], 50).Print()
        # df.Display(["b2_eta", "b2_phi", "b2_pt", "bjet2_idx", "bjet2_partFlav"], 50).Print()

        df = df.Define("has_two_bjets", "(bjet1_idx != -1) && (bjet2_idx != -1) && (bjet1_idx != bjet2_idx)")
        print(f"[INFO] Total entries after filtering for events with two b-jets (pT > 10 GeV): {df.Filter("has_two_bjets").Count().GetValue()}")

        # Acceptance of NGT Scouting
        df = df.Define("pass_NGT", "DST_NGTScouting")

        ##############################################################
        # Define channels
        ##############################################################

        df = FindHHChannels(df)

        # ETAU
        df_etau = df.Filter("ch_etau")
        df_etau = FindGenFinalState(df_etau, "etau")
        L1_seeds = ["L1_pSingleEGEle51_final", "L1_pSingleTkEle36_final", "L1_pSingleIsoTkEle28_final", "L1_pPuppiTauTkIsoEle45_22_final"]
        HLT_paths = ["HLT_Ele32_WPTight_L1Seeded", "HLT_Ele30_WPTight_L1Seeded_LooseDeepTauPFTauHPS30_eta2p1_CrossL1"]
        df_etau = df_etau.Define("pass_L1", "{}".format(" || ".join(L1_seeds)))
        df_etau = df_etau.Define("pass_HLT", "{}".format(" || ".join(HLT_paths)))

        # MUTAU
        df_mutau = df.Filter("ch_mutau")
        df_mutau = FindGenFinalState(df_mutau, "mutau")
        L1_seeds = ["L1_pSingleTkMuon22_final", "L1_pPuppiTauTkMuon42_18_final"]
        HLT_paths = ["HLT_IsoMu24_FromL1TkMuon", "HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1"]
        df_mutau = df_mutau.Define("pass_L1", "{}".format(" || ".join(L1_seeds)))
        df_mutau = df_mutau.Define("pass_HLT", "{}".format(" || ".join(HLT_paths)))
        
        # TAUTAU
        df_tautau = df.Filter("ch_tautau")
        df_tautau = FindGenFinalState(df_tautau, "tautau")
        L1_seeds = ["L1_pDoublePuppiTau52_52_final"]
        HLT_paths = ["HLT_DoubleMediumDeepTauPFTauHPS35_eta2p1"]
        df_tautau = df_tautau.Define("pass_L1", "{}".format(" || ".join(L1_seeds)))
        df_tautau = df_tautau.Define("pass_HLT", "{}".format(" || ".join(HLT_paths)))

    ##############################################################
    # Prepare plotting variable
    ##############################################################

    variables_dict = {
        "mass": ["mass [GeV]", r"Mass [GeV]", 100, 0, 1000],
        "pt": ["p_{T} [GeV]", r"p_{T} [GeV]", 100, 0, 500],
        "eta": ["#eta", r"\eta", 100, -5, 5],
        "phi": ["#phi", r"\phi", 100, -3.14, 3.14]
    }

    common_obj_labels = {
        "HH": "HH",
        "Hbb": r"$H_{bb}$",
        "Htt": r"$H_{\tau\tau}$",
        "bjet1": r"$b-jet_1$",
        "bjet2": r"$b-jet_2$",
    }

    channel_obj_labels = {
        "etau": {"ele": r"$e$", "vistau": r"$\tau_{h}$"},
        "mutau": {"muon": r"$\mu$", "vistau": r"$\tau_{h}$"},
        "tautau": {"vistau1": r"$\tau_{h,1}$","vistau2": r"$\tau_{h,2}$"},
    }

    obj_with_mass = ["HH", "Hbb", "Htt"]

    selection_dict = {
        'All': ["All events", "#FEA201", "step", 1.0, 1],
        'PassL1': ["L1 acceptance", "#80CAFA", "fill", 0.5, 3],
        'PassHLT': ["HLT acceptance", "#009900", "fill", 0.5, 4],
        'PassNGT': ["NGT acceptance", "#9437FF", "fill", 0.5, 2],
    }

    if not args.skip_histos:

        ##############################################################
        # Save histograms to root file
        ##############################################################

        print(f"[INFO] Saving histograms to {histo_dir}/Acceptance.root")
        histos_file = ROOT.TFile(f"{histo_dir}/Acceptance.root", "RECREATE")

        for df_ch, channel in zip( [df_etau, df_mutau, df_tautau],
                                   ["etau", "mutau", "tautau"]):

            for selection, sel_name in zip( ["true", "pass_L1", "pass_HLT", "pass_NGT"],
                                            ["All", "PassL1", "PassHLT", "PassNGT"]):

                # Create subdirectory (mkdir with a path works from the file root)
                histo_subdir = histos_file.mkdir(f"Ch_{channel}/{sel_name}")
                histo_subdir.cd()

                histos = {}
                for var, (label_root, label_latex, bins, min_val, max_val) in variables_dict.items():
                    obj_labels = {**common_obj_labels, **channel_obj_labels[channel]}
                    objects = obj_labels.keys() if var != "mass" else [o for o in obj_labels if o in obj_with_mass]
                    for obj in objects:
                        histos[f"{obj}_{var}"] = df_ch.Filter(selection).Histo1D((f"{obj}_{var}", f"{obj}_{var};{obj_labels[obj]} {label_root};Events", bins, min_val, max_val), f"{obj}_{var}")

                for name, histo in sorted(histos.items()):
                    histo.Write()
                    print(f"[INFO] Saved histogram: {name}")

        histos_file.Close()

    ##############################################################
    # Plot histograms
    ##############################################################

    plots_dir = script_dir + "/" + args.plots_dir
    os.makedirs(plots_dir, exist_ok=True)
    print(f"[INFO] Output directory for plots: {plots_dir}")

    # Open root file with histograms
    histos_file = ROOT.TFile(f"{histo_dir}/Acceptance.root", "READ")

    for channel, ch_title in zip(   ["etau", "mutau", "tautau"],
                                    [r"$\tau_{e}\tau_{h}$", r"$\tau_{\mu}\tau_{h}$", r"$\tau_{h}\tau_{h}$"]):

        for var, (label_root, label_latex, bins, min_val, max_val) in variables_dict.items():
            obj_labels = {**common_obj_labels, **channel_obj_labels[channel]}
            objects = obj_labels.keys() if var != "mass" else [o for o in obj_labels if o in obj_with_mass]

            for i, obj in enumerate(objects):

                fig, ax = plt.subplots(1, figsize=(10,10))
                hep.cms.label("Preliminary", data=False, ax=ax, rlabel=r"$HH \rightarrow bb\tau\tau$ (200 PU)", fontsize=22)

                edges = np.linspace(min_val, max_val, bins + 1)

                for sel_name in ["All", "PassL1", "PassHLT", "PassNGT"]:
                    
                    hist = histos_file.Get(f"Ch_{channel}/{sel_name}/{obj}_{var}")
                    if not hist:
                        print(f"[WARNING] Histogram Ch_{channel}/{sel_name}/{obj}_{var} not found, skipping.")
                        continue

                    centers, contents, errors = hist_to_numpy(hist)
                    hep.histplot(contents, edges, ax=ax, color=selection_dict[sel_name][1], histtype=selection_dict[sel_name][2], alpha=selection_dict[sel_name][3], zorder=selection_dict[sel_name][4])
                    ax.errorbar(centers, contents, yerr=errors, fmt="o", markersize=3, capsize=2, color=selection_dict[sel_name][1], label=selection_dict[sel_name][0], zorder=selection_dict[sel_name][4])

                ax.set_xlabel(f"{obj_labels[obj]} {label_latex}")
                ax.set_ylabel("Events")
                ax.legend(frameon=False, loc="upper right", title=f"Channel {ch_title}", title_fontsize=20, fontsize=20, alignment="left")
                ax.set_xlim(min_val, max_val)
                ax.grid(True, alpha=0.75, linestyle="dashdot", linewidth=0.75)

                fig.tight_layout()

                out_path = f"{plots_dir}/Ch_{channel}_{obj}_{var}"
                print(f"[INFO] Saving plot: {out_path}")
                fig.savefig(out_path + ".png", dpi=150)
                fig.savefig(out_path + ".pdf", dpi=150)
                plt.close(fig)

    histos_file.Close()
