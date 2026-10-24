import ROOT
import glob, os, argparse, re
from pathlib import Path
import numpy as np

# Import the custom C++ functions from GenFunctions.cc
REPO_DIR = Path(__file__).resolve().parent
SRC = REPO_DIR  / "GenFunctions.cc"

# Load the custom C++ functions
ROOT.gInterpreter.AddIncludePath(str(REPO_DIR))
ROOT.gInterpreter.ProcessLine(f'#include "{SRC.name}"')

# Multi-threaded snapshot (could have conflicts with debug print-out)
ROOT.EnableImplicitMT()

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

def merge_hlt(base_dir_hlt, path_df, args):

    files_hlt_all = glob.glob(base_dir_hlt + "/step2_*.root")
    if args.max_files is not None:
        files_hlt_all = files_hlt_all[:args.max_files]

    files_hlt = files_with_events(files_hlt_all)
    chain_hlt = make_chain(files_hlt)
    df = ROOT.RDataFrame(chain_hlt)
    
    print(f"Total entries in chain HLT: {df.Count().GetValue()}")

    return df

# def merge_hlt_ngt(base_dir_hlt, base_dir_ngt, path_df, args):

#     files_hlt_all = sorted(glob.glob(base_dir_hlt + "/step2_*.root"))
#     files_ngt_all = sorted(glob.glob(base_dir_ngt + "/step2_*.root"))

#     if args.max_files is not None:
#         files_hlt_all = files_hlt_all[:args.max_files]
#         files_ngt_all = files_ngt_all[:args.max_files]

#     files_hlt = files_with_events(files_hlt_all)
#     files_ngt = files_with_events(files_ngt_all)

#     chain_hlt = make_chain(files_hlt)
#     chain_ngt = make_chain(files_ngt)
#     df_hlt = ROOT.RDataFrame(chain_hlt)
#     df_ngt = ROOT.RDataFrame(chain_ngt)

#     print(f"Total entries in chain HLT: {df_hlt.Count().GetValue()}")
#     print(f"Total entries in chain NGT: {df_ngt.Count().GetValue()}")

#     # NGT side: everything except HLT_*/L1_* (those come from the HLT file).
#     cols_ngt_filtered = [str(c) for c in df_ngt.GetColumnNames() if not (str(c).startswith("HLT_") or str(c).startswith("L1_"))]
#     print(f"[INFO] Keeping {len(cols_ngt_filtered)} NGT columns for merging.")
#     # HLT side: only HLT_*/L1_* without the _pHLT suffix.
#     cols_hlt_filtered = [str(c) for c in df_hlt.GetColumnNames() if ((str(c).startswith("HLT_") or str(c).startswith("L1_")) and not str(c).endswith("_pHLT"))]
#     print(f"[INFO] Keeping {len(cols_hlt_filtered)} HLT columns for merging.")

#     snapshot_options = ROOT.RDF.RSnapshotOptions()
#     snapshot_options.fCompressionAlgorithm = ROOT.RCompressionSetting.EAlgorithm.kLZ4
#     snapshot_options.fCompressionLevel = 4

#     # The two productions contain the same events but in DIFFERENT order.
#     # TChain::AddFriend (with or without a (run,event) index) does NOT work here:
#     # RDataFrame reads the friend POSITIONALLY and ignores the friend's TTreeIndex.
#     # The only exact method inside RDataFrame is an explicit (run,event) lookup:
#     # build a C++ map (run,event)->HLT row, then set each HLT column by lookup.
#     hlt_data = df_hlt.AsNumpy(["run", "event"] + cols_hlt_filtered)
#     keys = list(zip(hlt_data["run"].tolist(), hlt_data["event"].tolist()))
#     col_values = {c: hlt_data[c].tolist() for c in cols_hlt_filtered}

#     # Global C++ map: key = run*1e9 + event, value = row index in the HLT arrays.
#     ROOT.gInterpreter.Declare("#include <unordered_map>\n#include <vector>\nstd::unordered_map<long long, long long> g_hlt_row;")
#     fill = "\n".join(
#         f"g_hlt_row[(long long){int(r)}*1000000000LL + (long long){int(e)}] = {i}LL;"
#         for i, (r, e) in enumerate(keys)
#     )
#     ROOT.gInterpreter.ProcessLine(fill)

#     # For each HLT column, declare a C++ array of values and set it by lookup.
#     # Use Redefine where the NGT chain already has the branch, Define otherwise.
#     ngt_colnames = set(str(c) for c in df_ngt.GetColumnNames())
#     df = df_ngt
#     for c in cols_hlt_filtered:
#         vals = col_values[c]
#         arr_name = "g_hlt_" + c
#         if np.issubdtype(hlt_data[c].dtype, np.bool_):
#             cpp_type = "bool"
#         elif np.issubdtype(hlt_data[c].dtype, np.integer):
#             cpp_type = "int"
#         else:
#             cpp_type = "float"
#         decl = f"std::vector<{cpp_type}> {arr_name} = {{"
#         decl += ",".join((str(int(v)) if cpp_type != "float" else repr(float(v))) for v in vals)
#         decl += "};"
#         ROOT.gInterpreter.Declare(decl)
#         expr = f"""
#             long long key = (long long)run * 1000000000LL + (long long)event;
#             auto it = g_hlt_row.find(key);
#             return (it != g_hlt_row.end()) ? {arr_name}[it->second] : ({cpp_type})-1;
#         """
#         # Replace the NGT's own HLT value with the aligned HLT-file value.
#         df = df.Redefine(c, expr) if c in ngt_colnames else df.Define(c, expr)

#     snapshot_columns = ROOT.vector(str)()
#     for column in cols_ngt_filtered + cols_hlt_filtered:
#         snapshot_columns.push_back(column)

#     print(f"[INFO] Saving merged dataframe to {path_df}")
#     df.Snapshot("Events", path_df, snapshot_columns, snapshot_options)

#     return ROOT.RDataFrame("Events", path_df)

def FindHHGenObjects(df):

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

    return df

def FindHHChannels(df):

    df = (df
        .Define("tau1_decay_idx", "Get_tau_decay(sorted_Htt_decay_idxs[0], GenPart_pdgId, GenPart_statusFlags, GenPart_genPartIdxMother)")
        .Define("tau2_decay_idx", "Get_tau_decay(sorted_Htt_decay_idxs[1], GenPart_pdgId, GenPart_statusFlags, GenPart_genPartIdxMother)")
        .Define("ch_etau", "((tau1_decay_idx[0] == 0) && (tau2_decay_idx[0] == 2)) || ((tau1_decay_idx[0] == 2) && (tau2_decay_idx[0] == 0))")
        .Define("ch_mutau", "((tau1_decay_idx[0] == 1) && (tau2_decay_idx[0] == 2)) || ((tau1_decay_idx[0] == 2) && (tau2_decay_idx[0] == 1))")
        .Define("ch_tautau", "((tau1_decay_idx[0] == 2) && (tau2_decay_idx[0] == 2))")
    )

    return df

def FindGenFinalState(df, ch):

    if ch == "etau":
        df = (df
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
    )

    elif ch == "mutau":
        df = (df
            # index of the muon
            .Define("muon_idx", "(tau1_decay_idx[0] == 1) ? tau1_decay_idx[1] : tau2_decay_idx[1]")
            .Define("muon_pt", "GenPart_pt[muon_idx]")
            .Define("muon_eta", "GenPart_eta[muon_idx]")
            .Define("muon_phi", "GenPart_phi[muon_idx]")
            # index of the hadronic tau
            .Define("tauhad_idx", "(tau1_decay_idx[0] == 2) ? sorted_Htt_decay_idxs[0] : sorted_Htt_decay_idxs[1]")
            .Define("vistau_idx", "GetGenVisTau(tauhad_idx, GenVisTau_genPartIdxMother)")
            .Define("vistau_pt", "GenVisTau_pt[vistau_idx]")
            .Define("vistau_eta", "GenVisTau_eta[vistau_idx]")
            .Define("vistau_phi", "GenVisTau_phi[vistau_idx]")
            .Define("vistau_mass", "GenVisTau_mass[vistau_idx]")
        )

    elif ch == "tautau":
        df = (df
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
        )

    return df
    
def FindRecoMataching(df, ch, coll):

    df = (df
          # match gen bjet 1 to HLT bjet
          .Define("hlt_bjet1_idx", f"GetClosestIdx(bjet1_eta, bjet1_phi, {coll["hlt"]["bjet"]}_eta, {coll["hlt"]["bjet"]}_phi, 0.4)")
          .Define("hlt_bjet1_pt", f"{coll["hlt"]["bjet"]}_pt[hlt_bjet1_idx]")
          .Define("hlt_bjet1_eta", f"{coll["hlt"]["bjet"]}_eta[hlt_bjet1_idx]")
          .Define("hlt_bjet1_phi", f"{coll["hlt"]["bjet"]}_phi[hlt_bjet1_idx]")
          .Define("hlt_bjet1_tag", f"{coll["hlt"]["bjetTag"]}[hlt_bjet1_idx]")
          # match gen bjet 1 to L1 bjet
          .Define("l1_bjet1_idx", f"GetClosestIdx(bjet1_eta, bjet1_phi, {coll["l1"]["bjet"]}_eta, {coll["l1"]["bjet"]}_phi, 0.4)")
          .Define("l1_bjet1_pt", f"{coll["l1"]["bjet"]}_pt[l1_bjet1_idx]")
          .Define("l1_bjet1_eta", f"{coll["l1"]["bjet"]}_eta[l1_bjet1_idx]")
          .Define("l1_bjet1_phi", f"{coll["l1"]["bjet"]}_phi[l1_bjet1_idx]")
          .Define("l1_bjet1_tag", f"{coll["l1"]["bjetTag"]}[l1_bjet1_idx]")
          # match gen bjet 2 to HLT bjet
          .Define("hlt_bjet2_idx", f"GetClosestIdx(bjet2_eta, bjet2_phi, {coll["hlt"]["bjet"]}_eta, {coll["hlt"]["bjet"]}_phi, 0.4)")
          .Define("hlt_bjet2_pt", f"{coll["hlt"]["bjet"]}_pt[hlt_bjet2_idx]")
          .Define("hlt_bjet2_eta", f"{coll["hlt"]["bjet"]}_eta[hlt_bjet2_idx]")
          .Define("hlt_bjet2_phi", f"{coll["hlt"]["bjet"]}_phi[hlt_bjet2_idx]")
          .Define("hlt_bjet2_tag", f"{coll["hlt"]["bjetTag"]}[hlt_bjet2_idx]")
          # match gen bjet 2 to L1 bjet
          .Define("l1_bjet2_idx", f"GetClosestIdx(bjet2_eta, bjet2_phi, {coll["l1"]["bjet"]}_eta, {coll["l1"]["bjet"]}_phi, 0.4)")
          .Define("l1_bjet2_pt", f"{coll["l1"]["bjet"]}_pt[l1_bjet2_idx]")
          .Define("l1_bjet2_eta", f"{coll["l1"]["bjet"]}_eta[l1_bjet2_idx]")
          .Define("l1_bjet2_phi", f"{coll["l1"]["bjet"]}_phi[l1_bjet2_idx]")
          .Define("l1_bjet2_tag", f"{coll["l1"]["bjetTag"]}[l1_bjet2_idx]")
    )

    if ch == "etau":
        df = (df
            # match gen electron to HLT electron
            .Define("hlt_ele_idx", f"GetClosestIdx(ele_eta, ele_phi, {coll["hlt"]["ele"]}_eta, {coll["hlt"]["ele"]}_phi, 0.1)")
            .Define("hlt_ele_pt", f"{coll["hlt"]["ele"]}_pt[hlt_ele_idx]")
            .Define("hlt_ele_eta", f"{coll["hlt"]["ele"]}_eta[hlt_ele_idx]")
            .Define("hlt_ele_phi", f"{coll["hlt"]["ele"]}_phi[hlt_ele_idx]")
            # match gen electron to L1 electron
            .Define("l1_ele_idx", f"GetClosestIdx(ele_eta, ele_phi, {coll["l1"]["ele"]}_eta, {coll["l1"]["ele"]}_phi, 0.1)")
            .Define("l1_ele_pt", f"{coll["l1"]["ele"]}_pt[l1_ele_idx]")
            .Define("l1_ele_eta", f"{coll["l1"]["ele"]}_eta[l1_ele_idx]")
            .Define("l1_ele_phi", f"{coll["l1"]["ele"]}_phi[l1_ele_idx]")
            # match gen vis tau to HLT tau
            .Define("hlt_tau_idx", f"GetClosestIdx(vistau_eta, vistau_phi, {coll["hlt"]["tau"]}_eta, {coll["hlt"]["tau"]}_phi, 0.4)")
            .Define("hlt_tau_pt", f"{coll["hlt"]["tau"]}_pt[hlt_tau_idx]")
            .Define("hlt_tau_eta", f"{coll["hlt"]["tau"]}_eta[hlt_tau_idx]")
            .Define("hlt_tau_phi", f"{coll["hlt"]["tau"]}_phi[hlt_tau_idx]")
            .Define("hlt_tau_tag", f"{coll["hlt"]["tauTag"]}[hlt_tau_idx]")
            # match gen vis tau to L1 tau
            .Define("l1_tau_idx", f"GetClosestIdx(vistau_eta, vistau_phi, {coll["l1"]["tau"]}_eta, {coll["l1"]["tau"]}_phi, 0.4)")
            .Define("l1_tau_pt", f"{coll["l1"]["tau"]}_pt[l1_tau_idx]")
            .Define("l1_tau_eta", f"{coll["l1"]["tau"]}_eta[l1_tau_idx]")
            .Define("l1_tau_phi", f"{coll["l1"]["tau"]}_phi[l1_tau_idx]")
            .Define("l1_tau_tag", f"{coll["l1"]["tauTag"]}[l1_tau_idx]")
        )
    elif ch == "mutau":
        df = (df
            # match gen muon to HLT muon
            .Define("hlt_muon_idx", f"GetClosestIdx(muon_eta, muon_phi, {coll["hlt"]["muon"]}_eta, {coll["hlt"]["muon"]}_phi, 0.1)")
            .Define("hlt_muon_pt", f"{coll["hlt"]["muon"]}_pt[hlt_muon_idx]")
            .Define("hlt_muon_eta", f"{coll["hlt"]["muon"]}_eta[hlt_muon_idx]")
            .Define("hlt_muon_phi", f"{coll["hlt"]["muon"]}_phi[hlt_muon_idx]")
            # match gen muon to L1 muon
            .Define("l1_muon_idx", f"GetClosestIdx(muon_eta, muon_phi, {coll["l1"]["muon"]}_eta, {coll["l1"]["muon"]}_phi, 0.1)")
            .Define("l1_muon_pt", f"{coll["l1"]["muon"]}_pt[l1_muon_idx]")
            .Define("l1_muon_eta", f"{coll["l1"]["muon"]}_eta[l1_muon_idx]")
            .Define("l1_muon_phi", f"{coll["l1"]["muon"]}_phi[l1_muon_idx]")
            # match gen vis tau to HLT tau
            .Define("hlt_tau_idx", f"GetClosestIdx(vistau_eta, vistau_phi, {coll["hlt"]["tau"]}_eta, {coll["hlt"]["tau"]}_phi, 0.4)")
            .Define("hlt_tau_pt", f"{coll["hlt"]["tau"]}_pt[hlt_tau_idx]")
            .Define("hlt_tau_eta", f"{coll["hlt"]["tau"]}_eta[hlt_tau_idx]")
            .Define("hlt_tau_phi", f"{coll["hlt"]["tau"]}_phi[hlt_tau_idx]")
            .Define("hlt_tau_tag", f"{coll["hlt"]["tauTag"]}[hlt_tau_idx]")
            # match gen vis tau to L1 tau
            .Define("l1_tau_idx", f"GetClosestIdx(vistau_eta, vistau_phi, {coll["l1"]["tau"]}_eta, {coll["l1"]["tau"]}_phi, 0.4)")
            .Define("l1_tau_pt", f"{coll["l1"]["tau"]}_pt[l1_tau_idx]")
            .Define("l1_tau_eta", f"{coll["l1"]["tau"]}_eta[l1_tau_idx]")
            .Define("l1_tau_phi", f"{coll["l1"]["tau"]}_phi[l1_tau_idx]")
            .Define("l1_tau_tag", f"{coll["l1"]["tauTag"]}[l1_tau_idx]")
        )
    elif ch == "tautau":
        df = (df
            # match gen vis tau 1 to HLT tau
            .Define("hlt_tau1_idx", f"GetClosestIdx(vistau1_eta, vistau1_phi, {coll["hlt"]["tau"]}_eta, {coll["hlt"]["tau"]}_phi, 0.4)")
            .Define("hlt_tau1_pt", f"{coll["hlt"]["tau"]}_pt[hlt_tau1_idx]")
            .Define("hlt_tau1_eta", f"{coll["hlt"]["tau"]}_eta[hlt_tau1_idx]")
            .Define("hlt_tau1_phi", f"{coll["hlt"]["tau"]}_phi[hlt_tau1_idx]")
            .Define("hlt_tau1_tag", f"{coll["hlt"]["tauTag"]}[hlt_tau1_idx]")
            # match gen vis tau 1 to L1 tau
            .Define("l1_tau1_idx", f"GetClosestIdx(vistau1_eta, vistau1_phi, {coll["l1"]["tau"]}_eta, {coll["l1"]["tau"]}_phi, 0.4)")
            .Define("l1_tau1_pt", f"{coll["l1"]["tau"]}_pt[l1_tau1_idx]")
            .Define("l1_tau1_eta", f"{coll["l1"]["tau"]}_eta[l1_tau1_idx]")
            .Define("l1_tau1_phi", f"{coll["l1"]["tau"]}_phi[l1_tau1_idx]")
            .Define("l1_tau1_tag", f"{coll["l1"]["tauTag"]}[l1_tau1_idx]")
            # match gen vis tau 2 to HLT tau
            .Define("hlt_tau2_idx", f"GetClosestIdx(vistau2_eta, vistau2_phi, {coll["hlt"]["tau"]}_eta, {coll["hlt"]["tau"]}_phi, 0.4)")
            .Define("hlt_tau2_pt", f"{coll["hlt"]["tau"]}_pt[hlt_tau2_idx]")
            .Define("hlt_tau2_eta", f"{coll["hlt"]["tau"]}_eta[hlt_tau2_idx]")
            .Define("hlt_tau2_phi", f"{coll["hlt"]["tau"]}_phi[hlt_tau2_idx]")
            .Define("hlt_tau2_tag", f"{coll["hlt"]["tauTag"]}[hlt_tau2_idx]")
            # match gen vis tau 2 to L1 tau
            .Define("l1_tau2_idx", f"GetClosestIdx(vistau2_eta, vistau2_phi, {coll["l1"]["tau"]}_eta, {coll["l1"]["tau"]}_phi, 0.4)")
            .Define("l1_tau2_pt", f"{coll["l1"]["tau"]}_pt[l1_tau2_idx]")
            .Define("l1_tau2_eta", f"{coll["l1"]["tau"]}_eta[l1_tau2_idx]")
            .Define("l1_tau2_phi", f"{coll["l1"]["tau"]}_phi[l1_tau2_idx]")
            .Define("l1_tau2_tag", f"{coll["l1"]["tauTag"]}[l1_tau2_idx]")
        )

    return df