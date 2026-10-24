import matplotlib.pyplot as plt
import mplhep as hep
plt.style.use(hep.style.CMS)

from Utils import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Arguments for ReconstructionEfficiency.py')
    parser.add_argument('--in-dir', type=str, default='./LaunchReprocessing/DeepTau/NGTMenu', help='Input directory to step2 rot files with NGT menu.')
    parser.add_argument('--max-files', type=int, default=None, help='Maximum number of files to process.')
    parser.add_argument('--skip-histos', action='store_true', required=False, help='Skip histogram creation.')
    parser.add_argument('--histo-dir', default='Dataframes', help='Output directory for the merged dataframe and histograms.')
    parser.add_argument('--plots-dir', default='Plots_RecoEff', help='Output directory for the plots.')
    parser.add_argument('--tau-reco', type=str, choices=['DeepTau', 'ParT'], default='DeepTau', help='Tau reconstruction strateggy (default: %(default)s).')
    args = parser.parse_args()

    tau_reco = args.tau_reco
    script_dir = os.path.dirname(os.path.abspath(__file__))
    histo_dir = script_dir + "/Output/" + args.histo_dir
    os.makedirs(histo_dir, exist_ok=True)
    print(f"[INFO] Output directory for the merged dataframe and histograms: {histo_dir}")

    ##############################################################
    # Prepare the merged dataframe from NGT and HLT input files
    ##############################################################

    path_df = f"{histo_dir}/df_ngt_{tau_reco}.root"

    df_etau = df_mutau = df_tautau = None

    base_dir_ngt = args.in_dir
    print(f"[INFO] Reading NGT root files from {base_dir_ngt}")
    df = merge_hlt(base_dir_ngt, path_df, args)

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
        
        # MUTAU
        df_mutau = df.Filter("ch_mutau")
        df_mutau = FindGenFinalState(df_mutau, "mutau")
        df_mutau = FindRecoMataching(df_mutau, "mutau", collection_dict)
        
        # TAUTAU
        df_tautau = df.Filter("ch_tautau")
        df_tautau = FindGenFinalState(df_tautau, "tautau")
        df_tautau = FindRecoMataching(df_tautau, "tautau", collection_dict)

        # # DEBUG
        # print(f"[INFO] Events in etau channel: {df_etau.Count().GetValue()}")
        # df_etau = df_etau.Define("has_2genbjets", "(bjet1_idx != -1) && (bjet2_idx != -1) && (bjet1_idx != bjet2_idx)")
        # print(f"[INFO] Events with two gen b-jets (pT > 10 GeV): {df_etau.Filter("has_2genbjets").Count().GetValue()}")
        # df_etau = df_etau.Define("has_2hltbjets", "(hlt_bjet1_idx != -1) && (hlt_bjet2_idx != -1)")
        # print(f"[INFO] Events with two b-jets: {df_etau.Filter("has_2hltbjets").Count().GetValue()}")
        # df_etau = df_etau.Define("has_hltele", "(hlt_ele_idx != -1)")
        # print(f"[INFO] Events with one electron: {df_etau.Filter("has_hltele").Count().GetValue()}")
        # df_etau = df_etau.Define("has_hlttau", "(hlt_tau_idx != -1)")
        # print(f"[INFO] Events with one tau: {df_etau.Filter("has_hlttau").Count().GetValue()}")
        # print(f"[INFO] Events with two b-jets, one electron, one tau: {df_etau.Filter("has_2hltbjets && hlt_ele_idx && hlt_tau_idx").Count().GetValue()}")

    # triggers = ['l1', 'hlt']
    triggers = ['hlt']
    tau_wp = 0.5
    bjet_wp = 0.5

    common_gen_obj_dict = {
        "HH": {"name": "HH", "label": r"Gen HH",},
    }

    variables_dict = {
        "mass": ["mass [GeV]", r"Mass [GeV]", 50, 0, 1000],
        "pt": ["p_{T} [GeV]", r"$p_{T}$ [GeV]", 50, 0, 500],
        "eta": ["#eta", r"$\eta$", 50, -5, 5],
        "phi": ["#phi", r"$\phi$", 50, -3.14, 3.14]
    }

    obj_with_mass = ["HH"]

    channels_dict = {
        "etau": {
            "df": df_etau,
            "label": r"$\tau_{e}\tau_{h}$",
            "reco_obj": {
                "reco_dau1": {"name": "{trg}_ele", "label": r"Reco $e$",},
                "reco_dau2": {"name": "{trg}_tau", "label": r"Reco $\tau$",},
                "reco_b1": {"name": "{trg}_bjet1", "label": r"Reco $b-jet_1$",},
                "reco_b2": {"name": "{trg}_bjet2", "label": r"Reco $b-jet_2$",},
            },
            "gen_obj": {
                "dau1": {"name": "ele", "label": r"Gen $e$",},
                "dau2": {"name": "vistau", "label": r"Gen Vis $\tau_{h}$",},
                "b1": {"name": "bjet1", "label": r"Gen $b-jet_1$",},
                "b2": {"name": "bjet2", "label": r"Gen $b-jet_2$",},
           },
            "sel": {
                "All" : "true",
                "PassNGT" : "pass_NGT",
                "Reco_dau1" : "({trg}_ele_idx != -1)",
                "Reco_dau2" : "({trg}_tau_idx != -1)",
                "Reco_b1" : "({trg}_bjet1_idx != -1)",
                "Reco_b2" : "({trg}_bjet2_idx != -1)",
                "Reco_b" : "({trg}_bjet1_idx != -1) && ({trg}_bjet2_idx != -1)",
                "Reco_all" : "({trg}_ele_idx != -1) && ({trg}_tau_idx != -1) && ({trg}_bjet1_idx != -1) && ({trg}_bjet2_idx != -1)",
                "Reco_dau2_id" : "({trg}_tau_idx != -1) && ({trg}_tau_tag > {tau_wp})",
                "Reco_b1_id" : "({trg}_bjet1_idx != -1) && ({trg}_bjet1_tag > {bjet_wp})",
                "Reco_b2_id" : "({trg}_bjet2_idx != -1) && ({trg}_bjet2_tag > {bjet_wp})",
                "Reco_b_id" : "(({trg}_bjet1_idx != -1) && ({trg}_bjet1_tag > {bjet_wp})) && (({trg}_bjet2_idx != -1) && ({trg}_bjet2_tag > {bjet_wp}))",
                "Reco_all_dau_id" : "({trg}_ele_idx != -1) && ({trg}_tau_idx != -1) && ({trg}_tau_tag > {tau_wp}) && ({trg}_bjet1_idx != -1) && ({trg}_bjet2_idx != -1)",
                "Reco_all_id": "({trg}_ele_idx != -1) && ({trg}_tau_idx != -1) && ({trg}_bjet1_idx != -1) && ({trg}_bjet2_idx != -1) && ({trg}_tau_tag > {tau_wp}) && ({trg}_bjet1_tag > {bjet_wp}) && ({trg}_bjet2_tag > {bjet_wp})",
            },
            "sel_lists": {
                "EleRecoEff": ["PassNGT", "Reco_dau1"],
                "TauRecoEff": ["PassNGT", "Reco_dau2", "Reco_dau2_id"],
                "BRecoEff": ["PassNGT", "Reco_b", "Reco_b_id"],
                "AllObjRecoEff": ["PassNGT", "Reco_dau1", "Reco_dau2", "Reco_b", "Reco_all"],
                "AllObjRecoTagEff": ["PassNGT", "Reco_all", "Reco_all_dau_id", "Reco_all_id"],
            },
        },
        "mutau": {
            "df": df_mutau,
            "label": r"$\tau_{\mu}\tau_{h}$",
            "reco_obj": {
                "reco_dau1": {"name": "{trg}_muon", "label": r"Reco $\mu$",},
                "reco_dau2": {"name": "{trg}_tau", "label": r"Reco $\tau$",},
                "reco_b1": {"name": "{trg}_bjet1", "label": r"Reco $b-jet_1$",},
                "reco_b2": {"name": "{trg}_bjet2", "label": r"Reco $b-jet_2$",},
            },
            "gen_obj": {
                "dau1": {"name": "muon", "label": r"Gen $\mu$",},
                "dau2": {"name": "vistau", "label": r"Gen Vis $\tau_{h}$",},
                "b1": {"name": "bjet1", "label": r"Gen $b-jet_1$",},
                "b2": {"name": "bjet2", "label": r"Gen $b-jet_2$",},
            },
            "sel": {
                "All" : "true",
                "PassNGT" : "pass_NGT",
                "Reco_dau1" : "({trg}_muon_idx != -1)",
                "Reco_dau2" : "({trg}_tau_idx != -1)",
                "Reco_b1" : "({trg}_bjet1_idx != -1)",
                "Reco_b2" : "({trg}_bjet2_idx != -1)",
                "Reco_b" : "({trg}_bjet1_idx != -1) && ({trg}_bjet2_idx != -1)",
                "Reco_all" : "({trg}_muon_idx != -1) && ({trg}_tau_idx != -1) && ({trg}_bjet1_idx != -1) && ({trg}_bjet2_idx != -1)",
                "Reco_dau2_id" : "({trg}_tau_idx != -1) && ({trg}_tau_tag > {tau_wp})",
                "Reco_b1_id" : "({trg}_bjet1_idx != -1) && ({trg}_bjet1_tag > {bjet_wp})",
                "Reco_b2_id" : "({trg}_bjet2_idx != -1) && ({trg}_bjet2_tag > {bjet_wp})",
                "Reco_b_id" : "(({trg}_bjet1_idx != -1) && ({trg}_bjet1_tag > {bjet_wp})) && (({trg}_bjet2_idx != -1) && ({trg}_bjet2_tag > {bjet_wp}))",
                "Reco_all_dau_id" : "({trg}_muon_idx != -1) && ({trg}_tau_idx != -1) && ({trg}_tau_tag > {tau_wp}) && ({trg}_bjet1_idx != -1) && ({trg}_bjet2_idx != -1)",
                "Reco_all_id": "({trg}_muon_idx != -1) && ({trg}_tau_idx != -1) && ({trg}_bjet1_idx != -1) && ({trg}_bjet2_idx != -1) && ({trg}_tau_tag > {tau_wp}) && ({trg}_bjet1_tag > {bjet_wp}) && ({trg}_bjet2_tag > {bjet_wp})",
            },
            "sel_lists": {
                "MuRecoEff": ["PassNGT", "Reco_dau1"],
                "TauRecoEff": ["PassNGT", "Reco_dau2", "Reco_dau2_id"],
                "BRecoEff": ["PassNGT", "Reco_b", "Reco_b_id"],
                "AllObjRecoEff": ["PassNGT", "Reco_dau1", "Reco_dau2", "Reco_b", "Reco_all"],
                "AllObjRecoTagEff": ["PassNGT", "Reco_all", "Reco_all_dau_id", "Reco_all_id"],
            },
        },
        "tautau": {
            "df": df_tautau,
            "label": r"$\tau_{h}\tau_{h}$",
            "reco_obj": {
                "reco_dau1": {"name": "{trg}_tau1", "label": r"Reco leading $\tau$",},
                "reco_dau2": {"name": "{trg}_tau2", "label": r"Reco sub-leading $\tau$",},
                "reco_b1": {"name": "{trg}_bjet1", "label": r"Reco $b-jet_1$",},
                "reco_b2": {"name": "{trg}_bjet2", "label": r"Reco $b-jet_2$",},
            },
            "gen_obj": {
                "dau1": {"name": "vistau1", "label": r"Gen Vis $\tau_{h,1}$",},
                "dau2": {"name": "vistau2", "label": r"Gen Vis $\tau_{h,2}$",},
                "b1": {"name": "bjet1", "label": r"Gen $b-jet_1$",},
                "b2": {"name": "bjet2", "label": r"Gen $b-jet_2$",},
            },
            "sel": {
                "All" : "true",
                "PassNGT" : "pass_NGT",
                "Reco_dau1" : "({trg}_tau1_idx != -1)",
                "Reco_dau2" : "({trg}_tau2_idx != -1)",
                "Reco_daus" : "({trg}_tau1_idx != -1) && ({trg}_tau2_idx != -1)",
                "Reco_b1" : "({trg}_bjet1_idx != -1)",
                "Reco_b2" : "({trg}_bjet2_idx != -1)",
                "Reco_b" : "({trg}_bjet1_idx != -1) && ({trg}_bjet2_idx != -1)",
                "Reco_all" : "({trg}_tau1_idx != -1) && ({trg}_tau2_idx != -1) && ({trg}_bjet1_idx != -1) && ({trg}_bjet2_idx != -1)",
                "Reco_dau1_id" : "({trg}_tau1_idx != -1) && ({trg}_tau1_tag > {tau_wp})",
                "Reco_dau2_id" : "({trg}_tau2_idx != -1) && ({trg}_tau2_tag > {tau_wp})",
                "Reco_daus_id" : "(({trg}_tau1_idx != -1) && ({trg}_tau1_tag > {tau_wp})) && (({trg}_tau2_idx != -1) && ({trg}_tau2_tag > {tau_wp}))",
                "Reco_b1_id" : "({trg}_bjet1_idx != -1) && ({trg}_bjet1_tag > {bjet_wp})",
                "Reco_b2_id" : "({trg}_bjet2_idx != -1) && ({trg}_bjet2_tag > {bjet_wp})",
                "Reco_b_id" : "(({trg}_bjet1_idx != -1) && ({trg}_bjet1_tag > {bjet_wp})) && (({trg}_bjet2_idx != -1) && ({trg}_bjet2_tag > {bjet_wp}))",
                "Reco_all_dau_id" : "({trg}_tau1_idx != -1) && ({trg}_tau2_idx != -1) && ({trg}_tau1_tag > {tau_wp}) && ({trg}_tau2_tag > {tau_wp}) && ({trg}_bjet1_idx != -1) && ({trg}_bjet2_idx != -1)",
                "Reco_all_id": "({trg}_tau1_idx != -1) && ({trg}_tau2_idx != -1) && ({trg}_bjet1_idx != -1) && ({trg}_bjet2_idx != -1) && ({trg}_tau1_tag > {tau_wp}) && ({trg}_tau2_tag > {tau_wp}) && ({trg}_bjet1_tag > {bjet_wp}) && ({trg}_bjet2_tag > {bjet_wp})",
            },
            "sel_lists": {
                "TauRecoEff": ["PassNGT", "Reco_dau1", "Reco_daus", "Reco_daus_id"],
                "BRecoEff": ["PassNGT", "Reco_b", "Reco_b_id"],
                "AllObjRecoEff": ["PassNGT", "Reco_dau1", "Reco_dau2", "Reco_b", "Reco_all"],
                "AllObjRecoTagEff": ["PassNGT", "Reco_all", "Reco_all_dau_id", "Reco_all_id"],
            },
        },
    }

    selection_dict = {
        'All': {'label': "All events",      'color': "#9c9ca1", 'hist': "step", 'alpha': 1.0,   'zorder': 1,    },
        'PassNGT': {'label': "NGT acceptance",  'color': "#7a21dd", 'hist': "step", 'alpha': 1.0,   'zorder': 2,    },
        'Reco_dau1': {'label': "Reconstructed {dau1}",  'color': "#ffa90e", 'hist': "fill", 'alpha': 0.5,   'zorder': 3,    },
        'Reco_dau2': {'label': "Reconstructed {dau2}",  'color': "#99670a", 'hist': "fill", 'alpha': 0.5,   'zorder': 4,    },
        'Reco_daus': {'label': r"Reconstructed $\tau$'s",  'color': "#e76300", 'hist': "fill", 'alpha': 0.5,   'zorder': 5,    },
        'Reco_b1': {'label': r"Reconstructed $b_1$",  'color': "#33B819", 'hist': "fill", 'alpha': 0.5,   'zorder': 6,    },
        'Reco_b2': {'label': r"Reconstructed $b_2$",  'color': "#0E6734", 'hist': "fill", 'alpha': 0.5,   'zorder': 7,    },
        'Reco_b': {'label': "Reconstructed b-jets",  'color': "#159E3E", 'hist': "fill", 'alpha': 0.5,   'zorder': 8,    },
        'Reco_all': {'label': "Reconstructed all objects",  'color': "#3f90da", 'hist': "fill", 'alpha': 0.5,   'zorder': 9,    },
        'Reco_dau1_id': {'label': "Reconstructed + ID {dau1}",  'color': "#7b1500", 'hist': "fill", 'alpha': 0.5,   'zorder': 10,    },
        'Reco_dau2_id': {'label': "Reconstructed + ID {dau2}",  'color': "#4e0d00", 'hist': "fill", 'alpha': 0.5,   'zorder': 11,    },
        'Reco_daus_id': {'label': r"Reconstructed + ID $\tau$'s",  'color': "#bd1f01", 'hist': "fill", 'alpha': 0.5,   'zorder': 12,    },
        'Reco_b1_id': {'label': r"Reconstructed + ID $b_1$",  'color': "#FF8437", 'hist': "fill", 'alpha': 0.5,   'zorder': 13,    },
        'Reco_b2_id': {'label': r"Reconstructed + ID $b_2$",  'color': "#FFCA37", 'hist': "fill", 'alpha': 0.5,   'zorder': 14,    },
        'Reco_b_id': {'label': "Reconstructed + ID b-jets",  'color': "#00A783", 'hist': "fill", 'alpha': 0.5,   'zorder': 15,    },
        'Reco_all_dau_id': {'label': r"Reconstructed all objects + ID $\tau$'s",  'color': "#0E6734", 'hist': "fill", 'alpha': 0.5,   'zorder': 16,    },
        'Reco_all_id': {'label': r"Reconstructed + ID $\tau$'s + ID b-jets",  'color': "#2237F3", 'hist': "fill", 'alpha': 0.5,   'zorder': 17,    },
    }   

    if not args.skip_histos:

        ##############################################################
        # Save histograms to root file
        ##############################################################

        print(f"[INFO] Saving histograms to {histo_dir}/histos_reco_{tau_reco}.root")
        histos_file = ROOT.TFile(f"{histo_dir}/histos_reco_{tau_reco}.root", "RECREATE")

        for channel in channels_dict.keys():

            df_ch = channels_dict[channel]["df"]
            channel_dir = histos_file.mkdir(f"Ch_{channel}")

            for sel_name in channels_dict[channel]["sel"].keys():

                # Create subdirectory (mkdir with a path works from the file root)
                histo_subdir = channel_dir.mkdir(f"{sel_name}")

                for trigger in triggers:

                    selection_def = channels_dict[channel]["sel"][sel_name].format(trg=trigger, tau_wp=tau_wp, bjet_wp=bjet_wp)

                    histos = {}

                    # objects = {**channels_dict[channel]["reco_obj"], **channels_dict[channel]["gen_obj"], **common_gen_obj_dict}
                    # objects = {**channels_dict[channel]["gen_obj"], **common_gen_obj_dict}
                    objects = {**common_gen_obj_dict}
                    for object in objects:

                        obj = objects[object]["name"].format(trg=trigger)
                        obj_label = objects[object]["label"]
                        
                        for var, (label_root, label_latex, bins, min_val, max_val) in variables_dict.items():
                        
                            if var == "mass" and obj not in obj_with_mass: continue
    
                            h_name = f"{obj}_{var}"
                            histos[h_name] = df_ch.Filter(selection_def).Histo1D((h_name, f"{h_name};{obj_label} {label_root};Events", bins, min_val, max_val), f"{h_name}")

                    for name, histo in sorted(histos.items()):
                        histo_subdir.WriteObject(histo.GetValue(), name)
                        # print(f"[DEBUG] Saved histogram: Ch_{channel}/{sel_name}/{name}")

        histos_file.Close()

    ##############################################################
    # Plot histograms
    ##############################################################

    plots_dir = script_dir + "/Output/" + args.plots_dir + "_" + tau_reco
    os.makedirs(plots_dir, exist_ok=True)
    print(f"[INFO] Output directory for plots: {plots_dir}")

    # Open root file with histograms
    histos_file = ROOT.TFile(f"{histo_dir}/histos_reco_{tau_reco}.root", "READ")

    for channel in channels_dict.keys():

        plots_dir_ch = plots_dir + "/" + channel
        os.makedirs(plots_dir_ch, exist_ok=True)

        ch_title = channels_dict[channel]["label"]

        for trigger in triggers:

            # objects = {**channels_dict[channel]["reco_obj"], **channels_dict[channel]["gen_obj"], **common_gen_obj_dict}
            # objects = {**channels_dict[channel]["gen_obj"], **common_gen_obj_dict}
            objects = {**common_gen_obj_dict}
            for object in objects:

                obj = objects[object]["name"].format(trg=trigger)
                obj_label = objects[object]["label"]

                for var, (label_root, label_latex, bins, min_val, max_val) in variables_dict.items():

                    if var == "mass" and obj not in obj_with_mass: continue

                    for sel_list in channels_dict[channel]["sel_lists"].keys():

                        os.makedirs(f"{plots_dir_ch}/{sel_list}", exist_ok=True)
                        selection_list = channels_dict[channel]["sel_lists"][sel_list]

                        fig, ax = plt.subplots(1, figsize=(10,10))
                        hep.cms.label("Preliminary", data=False, ax=ax, rlabel=r"$HH \rightarrow bb\tau\tau$ (200 PU)", fontsize=22)

                        edges = np.linspace(min_val, max_val, bins + 1)
                        den = max_count = 0

                        for i_sel, sel_name in enumerate(selection_list):

                            dau1 = channels_dict[channel]['reco_obj']['reco_dau1']['label'].split('Reco ')[1]
                            dau2 = channels_dict[channel]['reco_obj']['reco_dau2']['label'].split('Reco ')[1]
                            sel_label = selection_dict[sel_name]['label'].format(dau1=dau1, dau2=dau2)
                            sel_color = selection_dict[sel_name]['color']
                            hist = histos_file.Get(f"Ch_{channel}/{sel_name}/{obj}_{var}")
                            if not hist:
                                print(f"[WARNING] Histogram Ch_{channel}/{sel_name}/{obj}_{var} not found, skipping.")
                                continue

                            centers, contents, errors = hist_to_numpy(hist)
                            
                            if i_sel == 0: 
                                den = hist.GetEntries()
                                max_count = np.max(contents)

                            frac = hist.GetEntries() / den * 100

                            hep.histplot(contents, edges, ax=ax, color=sel_color, histtype=selection_dict[sel_name]['hist'], alpha=selection_dict[sel_name]['alpha'], zorder=selection_dict[sel_name]['zorder'])
                            ax.errorbar(centers, contents, yerr=errors, fmt="o", markersize=3, capsize=2, color=sel_color, zorder=selection_dict[sel_name]['zorder'], label=f"{sel_label} = {frac:.1f}%")

                        ax.set_xlabel(f"{obj_label} {label_latex}")
                        ax.set_ylabel("Events")
                        ax.legend(frameon=False, loc="upper right", title=f"Channel {ch_title} ({tau_reco})", title_fontsize=20, fontsize=20, alignment="left")
                        ax.set_xlim(min_val, max_val)
                        ax.set_ylim(0,1.2*max_count)
                        ax.grid(True, alpha=0.75, linestyle="dashdot", linewidth=0.75)

                        fig.tight_layout()

                        out_path = f"{plots_dir_ch}/{sel_list}/{obj}_{var}"
                        print(f"[INFO] Saving plot: {out_path}")
                        fig.savefig(out_path + ".png", dpi=150)
                        fig.savefig(out_path + ".pdf", dpi=150)
                        plt.close(fig)

    histos_file.Close()
