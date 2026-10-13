import ROOT
import glob, os, argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
plt.style.use(hep.style.CMS)

# Import the custom C++ functions from GenFunctions.cc
REPO_DIR = Path(__file__).resolve().parent
SRC = REPO_DIR  / "GenFunctions.cc"

# Load the custom C++ functions
ROOT.gInterpreter.AddIncludePath(str(REPO_DIR))
ROOT.gInterpreter.ProcessLine(f'#include "{SRC.name}"')

def files_with_events(file_names):
    good_files = []
    for file_name in file_names:
        root_file = ROOT.TFile.Open(file_name)
        if root_file and not root_file.IsZombie() and root_file.Get("Events"):
            good_files.append(file_name)
        if root_file:
            root_file.Close()
    return good_files

def make_chain(file_names):
    chain = ROOT.TChain("Events")
    for file_name in file_names:
        chain.Add(file_name)
    return chain

def hist_to_numpy(hist):
    n = hist.GetNbinsX()
    centers = np.array([hist.GetBinCenter(i) for i in range(1, n + 1)])
    contents = np.array([hist.GetBinContent(i) for i in range(1, n + 1)])
    errors = np.array([hist.GetBinError(i) for i in range(1, n + 1)])
    return centers, contents, errors

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

    if not args.skip_merging:

        base_dir_hlt = "/data/evernazz/NanoAOD/SummerStudent/2026_10_08/CMSSW_17_0_0_pre6/src/AAA_Test/OldProduction/HLTMenu_ParT/"
        base_dir_ngt = "/data/evernazz/NanoAOD/SummerStudent/2026_10_08/CMSSW_17_0_0_pre6/src/AAA_Test/OldProduction/NGTScoutingFullTracking/"

        files_hlt_all = glob.glob(base_dir_hlt + "/step2_*.root")
        files_ngt_all = glob.glob(base_dir_ngt + "/step2_*.root")

        if args.max_files is not None:
            files_hlt_all = files_hlt_all[:args.max_files]
            files_ngt_all = files_ngt_all[:args.max_files]

        files_hlt = files_with_events(files_hlt_all)
        files_ngt = files_with_events(files_ngt_all)

        chain_hlt = make_chain(files_hlt)
        chain_ngt = make_chain(files_ngt)

        df_hlt = ROOT.RDataFrame(chain_hlt)
        df_ngt = ROOT.RDataFrame(chain_ngt)

        print(f"Total entries in chain HLT: {df_hlt.Count().GetValue()}")
        print(f"Total entries in chain NGT: {df_ngt.Count().GetValue()}")

        cols_ngt_filtered = [str(c) for c in df_ngt.GetColumnNames() if not str(c).startswith("HLT_")]
        print(f"[INFO] Keeping {len(cols_ngt_filtered)} NGT columns for merging.")
        cols_hlt_filtered = [str(c) for c in df_hlt.GetColumnNames() if str(c).startswith("HLT_") and not str(c).endswith("_pHLT")]
        print(f"[INFO] Keeping {len(cols_hlt_filtered)} HLT columns for merging.")

        chain_ngt.AddFriend(chain_hlt)
        df = ROOT.RDataFrame(chain_ngt)

        snapshot_columns = ROOT.vector(str)()
        for column in cols_ngt_filtered + cols_hlt_filtered:
            snapshot_columns.push_back(column)

        print(f"[INFO] Saving merged dataframe")

        snapshot_options = ROOT.RDF.RSnapshotOptions()
        snapshot_options.fCompressionLevel = 4
        df.Snapshot("Events", f"{histo_dir}/df_ngt_hlt.root", snapshot_columns, snapshot_options)

    else:

        df = ROOT.RDataFrame("Events", f"{histo_dir}/df_ngt_hlt.root")

    # # DEBUG
    # print("Available branches: ")
    # for branch in df.GetColumnNames():
    #     print(branch)

    if not args.skip_histos:
        ##############################################################
        # Define gen-level variables for the analysis
        ##############################################################

        print(f"[INFO] Total entries in merged dataframe: {df.Count().GetValue()}")
        df = df.Define("HH_idxs", "Get_HH_idxs(GenPart_pdgId, GenPart_statusFlags)")
        df = df.Filter("HH_idxs[0] >= 0")
        print(f"[INFO] Total entries after filtering for events with two Higgs bosons: {df.Count().GetValue()}")

        df = (df

                # The two Higgs bosons in the event
                .Define("H1_pt", "GenPart_pt[HH_idxs[0]]")
                .Define("H1_eta", "GenPart_eta[HH_idxs[0]]")
                .Define("H1_phi", "GenPart_phi[HH_idxs[0]]")
                .Define("H2_pt", "GenPart_pt[HH_idxs[1]]")
                .Define("H2_eta", "GenPart_eta[HH_idxs[1]]")
                .Define("H2_phi", "GenPart_phi[HH_idxs[1]]")

                # Di-Higgs invariant mass and kinematics
                .Define("HH", "Get_diObject_P4(H1_pt, H1_eta, H1_phi, 125., H2_pt, H2_eta, H2_phi, 125.)")
                .Define("HH_mass", "HH.M()")
                .Define("HH_pt", "HH.Pt()")
                .Define("HH_eta", "HH.Eta()")
                .Define("HH_phi", "HH.Phi()")

                # single Higgs decay mode and kinematics
                .Define("H1_decay_idxs", "Get_H_decay_idxs(HH_idxs[0], GenPart_pdgId, GenPart_statusFlags, GenPart_genPartIdxMother)")
                .Define("H1_decay1_pdgId", "GenPart_pdgId[H1_decay_idxs[0]]")
                .Define("H1_decay2_pdgId", "GenPart_pdgId[H1_decay_idxs[1]]")
                .Define("H2_decay_idxs", "Get_H_decay_idxs(HH_idxs[1], GenPart_pdgId, GenPart_statusFlags, GenPart_genPartIdxMother)")
                .Define("H2_decay1_pdgId", "GenPart_pdgId[H2_decay_idxs[0]]")
                .Define("H2_decay2_pdgId", "GenPart_pdgId[H2_decay_idxs[1]]")

                .Define("Hbb_idx", "(abs(H1_decay1_pdgId) == 5 && abs(H1_decay2_pdgId) == 5) ? HH_idxs[0] : HH_idxs[1]")
                .Define("Hbb_pt", "GenPart_pt[Hbb_idx]")
                .Define("Hbb_eta", "GenPart_eta[Hbb_idx]")
                .Define("Hbb_phi", "GenPart_phi[Hbb_idx]")
                .Define("Hbb_mass", "GenPart_mass[Hbb_idx]")

                .Define("Htt_idx", "(abs(H1_decay1_pdgId) == 15 && abs(H1_decay2_pdgId) == 15) ? HH_idxs[0] : HH_idxs[1]")
                .Define("Htt_pt", "GenPart_pt[Htt_idx]")
                .Define("Htt_eta", "GenPart_eta[Htt_idx]")
                .Define("Htt_phi", "GenPart_phi[Htt_idx]")
                .Define("Htt_mass", "GenPart_mass[Htt_idx]")

                # Higgs tautau decay products
                .Define("Htt_decay_idxs", "Get_H_decay_idxs(Htt_idx, GenPart_pdgId, GenPart_statusFlags, GenPart_genPartIdxMother)")
                .Define("sorted_Htt_decay_idxs", "Sort_idxs(Htt_decay_idxs, GenPart_pt)")
                .Define("tau1_pt", "GenPart_pt[sorted_Htt_decay_idxs[0]]")
                .Define("tau1_eta", "GenPart_eta[sorted_Htt_decay_idxs[0]]")
                .Define("tau1_phi", "GenPart_phi[sorted_Htt_decay_idxs[0]]")
                .Define("tau2_pt", "GenPart_pt[sorted_Htt_decay_idxs[1]]")
                .Define("tau2_eta", "GenPart_eta[sorted_Htt_decay_idxs[1]]")
                .Define("tau2_phi", "GenPart_phi[sorted_Htt_decay_idxs[1]]")

                # Higgs bb decay products
                .Define("Hbb_decay_idxs", "Get_H_decay_idxs(Hbb_idx, GenPart_pdgId, GenPart_statusFlags, GenPart_genPartIdxMother)")
                .Define("sorted_Hbb_decay_idxs", "Sort_idxs(Hbb_decay_idxs, GenPart_pt)")
                .Define("b1_pt", "GenPart_pt[sorted_Hbb_decay_idxs[0]]")
                .Define("b1_eta", "GenPart_eta[sorted_Hbb_decay_idxs[0]]")
                .Define("b1_phi", "GenPart_phi[sorted_Hbb_decay_idxs[0]]")
                .Define("b2_pt", "GenPart_pt[sorted_Hbb_decay_idxs[1]]")
                .Define("b2_eta", "GenPart_eta[sorted_Hbb_decay_idxs[1]]")
                .Define("b2_phi", "GenPart_phi[sorted_Hbb_decay_idxs[1]]")

                # from b-quarks to gen b-jets 
                # (GenJet collection has intrincic cut for pt > 10 GeV)
                .Define("bjet1_idx", "GetClosestIdx(b1_eta, b1_phi, GenJet_eta, GenJet_phi, 0.4)")
                .Define("bjet2_idx", "GetClosestIdx(b2_eta, b2_phi, GenJet_eta, GenJet_phi, 0.4)")
                .Define("bjet1_pt", "GenJet_pt[bjet1_idx]")
                .Define("bjet1_eta", "GenJet_eta[bjet1_idx]")
                .Define("bjet1_phi", "GenJet_phi[bjet1_idx]")
                .Define("bjet1_mass", "GenJet_mass[bjet1_idx]")
                .Define("bjet1_partFlav", "GenJet_partonFlavour[bjet1_idx]")
                .Define("bjet2_pt", "GenJet_pt[bjet2_idx]")
                .Define("bjet2_eta", "GenJet_eta[bjet2_idx]")
                .Define("bjet2_phi", "GenJet_phi[bjet2_idx]")
                .Define("bjet2_mass", "GenJet_mass[bjet2_idx]")
                .Define("bjet2_partFlav", "GenJet_partonFlavour[bjet2_idx]")

        )

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

        df = (df
                .Define("tau1_decay_idx", "Get_tau_decay(sorted_Htt_decay_idxs[0], GenPart_pdgId, GenPart_statusFlags, GenPart_genPartIdxMother)")
                .Define("tau2_decay_idx", "Get_tau_decay(sorted_Htt_decay_idxs[1], GenPart_pdgId, GenPart_statusFlags, GenPart_genPartIdxMother)")
                .Define("ch_etau", "((tau1_decay_idx[0] == 0) && (tau2_decay_idx[0] == 2)) || ((tau1_decay_idx[0] == 2) && (tau2_decay_idx[0] == 0))")
                .Define("ch_mutau", "((tau1_decay_idx[0] == 1) && (tau2_decay_idx[0] == 2)) || ((tau1_decay_idx[0] == 2) && (tau2_decay_idx[0] == 1))")
                .Define("ch_tautau", "((tau1_decay_idx[0] == 2) && (tau2_decay_idx[0] == 2))")
        )

        # ETAU
        df_etau = df.Filter("ch_etau")
        L1_seeds = ["L1_pSingleEGEle51_final", "L1_pSingleTkEle36_final", "L1_pSingleIsoTkEle28_final", "L1_pPuppiTauTkIsoEle45_22_final"]
        HLT_paths = ["HLT_Ele32_WPTight_L1Seeded", "HLT_Ele30_WPTight_L1Seeded_LooseDeepTauPFTauHPS30_eta2p1_CrossL1"]
        df_etau = (df_etau
                # index of the electron
                .Define("ele_idx", "(tau1_decay_idx[0] == 0) ? tau1_decay_idx[1] : tau2_decay_idx[1]")
                .Define("ele_pt", "GenPart_pt[ele_idx]")
                .Define("ele_eta", "GenPart_eta[ele_idx]")
                .Define("ele_phi", "GenPart_phi[ele_idx]")
                # index of the hadronic tau
                .Define("tauhad_idx", "(tau1_decay_idx[0] == 2) ? sorted_Htt_decay_idxs[0] : sorted_Htt_decay_idxs[1]")
                .Define("vistau_idx", "GetGenVisTau(tauhad_idx, GenVisTau_genPartIdxMother)")
                .Define("vistau_pt", "GenVisTau_pt[vistau_idx]")
                .Define("vistau_eta", "GenVisTau_eta[vistau_idx]")
                .Define("vistau_phi", "GenVisTau_phi[vistau_idx]")
                .Define("vistau_mass", "GenVisTau_mass[vistau_idx]")
                # acceptance of L1 and HLT seeds
                .Define("pass_L1", "{}".format(" || ".join(L1_seeds)))
                .Define("pass_HLT", "{}".format(" || ".join(HLT_paths)))
        )

        # MUTAU
        df_mutau = df.Filter("ch_mutau")
        L1_seeds = ["L1_pSingleTkMuon22_final", "L1_pPuppiTauTkMuon42_18_final"]
        HLT_paths = ["HLT_IsoMu24_FromL1TkMuon", "HLT_IsoMu20_eta2p1_LooseDeepTauPFTauHPS27_eta2p1_CrossL1"]
        df_mutau = (df_mutau
                # index of the muon
                .Define("mu_idx", "(tau1_decay_idx[0] == 1) ? tau1_decay_idx[1] : tau2_decay_idx[1]")
                .Define("mu_pt", "GenPart_pt[mu_idx]")
                .Define("mu_eta", "GenPart_eta[mu_idx]")
                .Define("mu_phi", "GenPart_phi[mu_idx]")
                # index of the hadronic tau
                .Define("tauhad_idx", "(tau1_decay_idx[0] == 2) ? sorted_Htt_decay_idxs[0] : sorted_Htt_decay_idxs[1]")
                .Define("vistau_idx", "GetGenVisTau(tauhad_idx, GenVisTau_genPartIdxMother)")
                .Define("vistau_pt", "GenVisTau_pt[vistau_idx]")
                .Define("vistau_eta", "GenVisTau_eta[vistau_idx]")
                .Define("vistau_phi", "GenVisTau_phi[vistau_idx]")
                .Define("vistau_mass", "GenVisTau_mass[vistau_idx]")
                # acceptance of L1 and HLT seeds
                .Define("pass_L1", "{}".format(" || ".join(L1_seeds)))
                .Define("pass_HLT", "{}".format(" || ".join(HLT_paths)))
        )

        # TAUTAU
        df_tautau = df.Filter("ch_tautau")
        L1_seeds = ["L1_pDoublePuppiTau52_52_final"]
        HLT_paths = ["HLT_DoubleMediumDeepTauPFTauHPS35_eta2p1"]
        df_tautau = (df_tautau
                # index of the leading hadronic tau
                .Define("vistau1_idx", "GetGenVisTau(sorted_Htt_decay_idxs[0], GenVisTau_genPartIdxMother)")
                .Define("vistau1_pt", "GenVisTau_pt[vistau1_idx]")
                .Define("vistau1_eta", "GenVisTau_eta[vistau1_idx]")
                .Define("vistau1_phi", "GenVisTau_phi[vistau1_idx]")
                .Define("vistau1_mass", "GenVisTau_mass[vistau1_idx]")
                # index of the sub-leading hadronic tau
                .Define("vistau2_idx", "GetGenVisTau(sorted_Htt_decay_idxs[1], GenVisTau_genPartIdxMother)")
                .Define("vistau2_pt", "GenVisTau_pt[vistau2_idx]")
                .Define("vistau2_eta", "GenVisTau_eta[vistau2_idx]")
                .Define("vistau2_phi", "GenVisTau_phi[vistau2_idx]")
                .Define("vistau2_mass", "GenVisTau_mass[vistau2_idx]")
                # acceptance of L1 and HLT seeds
                .Define("pass_L1", "{}".format(" || ".join(L1_seeds)))
                .Define("pass_HLT", "{}".format(" || ".join(HLT_paths)))
        )

    ##############################################################
    # Save histograms to root file
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
        "etau": {
            "ele": r"$e$",
            "vistau": r"$\tau_{h}$",
        },
        "mutau": {
            "mu": r"$\mu$",
            "vistau": r"$\tau_{h}$",
        },
        "tautau": {
            "vistau1": r"$\tau_{h,1}$",
            "vistau2": r"$\tau_{h,2}$",
        },
    }

    obj_with_mass = ["HH", "Hbb", "Htt"]

    if not args.skip_histos:

        print(f"[INFO] Saving histograms to {histo_dir}/Acceptance.root")
        histos_file = ROOT.TFile(f"{histo_dir}/Acceptance.root", "RECREATE")

        for df_ch, channel in zip( [df_etau, df_mutau, df_tautau],
                                   ["etau", "mutau", "tautau"]):

            for selection, sel_name in zip( ["true", "pass_L1", "pass_HLT", "pass_NGT"],
                                            ["All", "PassL1", "PassHLT", "PassNGT"]):

                # Create subdirectory
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

    selection_dict = {
        'All': ["All events", "#FEA201", "step", 1.0, 1],
        'PassL1': ["L1 acceptance", "#80CAFA", "fill", 0.5, 3],
        'PassHLT': ["HLT acceptance", "#009900", "fill", 0.5, 4],
        'PassNGT': ["NGT acceptance", "#9437FF", "fill", 0.5, 2],
    }

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
