import ROOT
import glob, os, argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

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

        base_dir_hlt = "/data/evernazz/NanoAOD/SummerStudent/2026_10_08/CMSSW_17_0_0_pre6/src/AAA_Test/HLTMenu_ParT/"
        base_dir_ngt = "/data/evernazz/NanoAOD/SummerStudent/2026_10_08/CMSSW_17_0_0_pre6/src/AAA_Test/NGTScoutingFullTracking/"

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

    )

    ##############################################################
    # Define channels and visible decay products
    ##############################################################

    df = (
        df
        .Define("tau1_decay_idx", "Get_tau_decay(sorted_Htt_decay_idxs[0], GenPart_pdgId, GenPart_statusFlags, GenPart_genPartIdxMother)")
        .Define("tau2_decay_idx", "Get_tau_decay(sorted_Htt_decay_idxs[1], GenPart_pdgId, GenPart_statusFlags, GenPart_genPartIdxMother)")

        .Define("ch_etau", "((tau1_decay_idx[0] == 0) && (tau2_decay_idx[0] == 2)) || ((tau1_decay_idx[0] == 2) && (tau2_decay_idx[0] == 0))")
        .Define("ch_mutau", "((tau1_decay_idx[0] == 1) && (tau2_decay_idx[0] == 2)) || ((tau1_decay_idx[0] == 2) && (tau2_decay_idx[0] == 1))")
        .Define("ch_tautau", "((tau1_decay_idx[0] == 2) && (tau2_decay_idx[0] == 2))")
    )

    # DEBUG
    df.Display(["tau1_decay_idx", "tau2_decay_idx", "ch_etau", "ch_mutau", "ch_tautau"], 50).Print()

    ##############################################################
    # Save histograms to root file
    ##############################################################

    variables_dict = {
        "mass": ["mass [GeV]", r"Mass [GeV]", 100, 0, 1000],
        "pt": ["p_{T} [GeV]", r"p_{T} [GeV]", 100, 0, 500],
        "eta": ["#eta", r"\eta", 100, -5, 5],
        "phi": ["#phi", r"\phi", 100, -3.14, 3.14]
    }

    obj_labels = {
        "HH": "HH", 
        "Hbb": r"$H_{bb}$", 
        "Htt": r"$H_{\tau\tau}$",
        "tau1": r"$\tau_1$", 
        "tau2": r"$\tau_2$",
        "b1": r"$b_1$", 
        "b2": r"$b_2$",
    }

    obj_with_mass = ["HH", "Hbb", "Htt"]

    if not args.skip_histos:

        print(f"[INFO] Saving histograms to {histo_dir}/Acceptance.root")
        histos_file = ROOT.TFile(f"{histo_dir}/Acceptance.root", "RECREATE")

        # Create subdirectory
        histo_subdir = histos_file.mkdir("Inclusive/All")
        histo_subdir.cd()

        histos = {}

        for var, (label_root, label_latex, bins, min_val, max_val) in variables_dict.items():

            objects = obj_labels.keys() if var != "mass" else ["HH", "Hbb", "Htt"]

            for obj in objects:

                histos[f"{obj}_{var}"] = df.Histo1D((f"{obj}_{var}", f"{obj}_{var};{obj_labels[obj]} {label_root};Events", bins, min_val, max_val), f"{obj}_{var}")

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

    for var, (label_root, label_latex, bins, min_val, max_val) in variables_dict.items():

        objects = obj_labels.keys() if var != "mass" else ["HH", "Hbb", "Htt"]

        for i, obj in enumerate(objects):

            fig, ax = plt.subplots(1, figsize=(10,10))

            hist = histos_file.Get(f"Inclusive/All/{obj}_{var}")
            if not hist:
                print(f"[WARNING] Histogram Inclusive/All/{obj}_{var} not found, skipping.")
                continue

            centers, contents, errors = hist_to_numpy(hist)
            ax.errorbar(centers, contents, yerr=errors, fmt="o", markersize=3, capsize=2, color="black", label="Gen")
            ax.set_xlabel(f"{obj_labels[obj]} {label_latex}")
            ax.set_ylabel("Events")
            ax.legend(frameon=False)
            ax.set_xlim(min_val, max_val)

            fig.tight_layout()

            out_path = f"{plots_dir}/Acceptance_{obj}_{var}"
            print(f"[INFO] Saving plot: {out_path}")
            fig.savefig(out_path + ".png", dpi=150)
            fig.savefig(out_path + ".pdf", dpi=150)
            plt.close(fig)

    histos_file.Close()
