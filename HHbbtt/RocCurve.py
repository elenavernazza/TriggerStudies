import matplotlib.pyplot as plt
import mplhep as hep
plt.style.use(hep.style.CMS)

from Utils import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Arguments for RocCurve.py')
    parser.add_argument('--in-dir-sig', type=str, default='./HHbbtt/NGTMenu_DeepTau_FullTracking/OutNano', help='Input directory to step2 rot files with NGT menu.')
    parser.add_argument('--in-dir-bkg', type=str, default='./QCD_Pt-15To3000/NGTMenu_DeepTau_FullTracking/OutNano', help='Input directory to step2 rot files with NGT menu.')
    parser.add_argument('--max-files', type=int, default=None, help='Maximum number of files to process.')
    parser.add_argument('--skip-histos', action='store_true', required=False, help='Skip histogram creation.')
    parser.add_argument('--histo-dir', default='Dataframes', help='Output directory for the merged dataframe and histograms.')
    parser.add_argument('--plots-dir', default='Plots_RocCurve', help='Output directory for the plots.')
    parser.add_argument('--tau-reco', type=str, choices=['DeepTau', 'ParT'], default='DeepTau', help='Tau reconstruction strateggy (default: %(default)s).')
    parser.add_argument('--tagger', type=str, choices=['tau', 'btag'], default='tau', help='Which tagger ROC to produce: tau ID or b-tag ID (default: %(default)s).')
    parser.add_argument('--wps', type=float, nargs='+', default=[], help='Score threshold(s) to mark on the ROC curve, e.g. --wps 0.5 0.65 0.8.')
    parser.add_argument('--ratio-plot', action='store_true', help='Add ratio plot in the bottom pannel.')
    args = parser.parse_args()

    tau_reco = args.tau_reco
    tagger = args.tagger

    # Mode-specific configuration
    if tagger == 'tau':
        score_name = "hltHpsPFTau_deepTauVSjet" if tau_reco == "DeepTau" else "hltAK4PuppiJet_ParT_TauvsAll"
        mode_label = tau_reco
        sig_obj_label = r"Genuine $\tau_h$"
        bkg_obj_label = r"Fake $\tau_h$"
    else:  # btag
        score_name = "hltAK4PuppiJet_DeepFlavour_prob_b"
        mode_label = "DeepJet"
        sig_obj_label = r"Genuine $b$-jet"
        bkg_obj_label = r"Fake $b$-jet"

    min_val = 0; max_val = 1; bins = 50

    script_dir = os.path.dirname(os.path.abspath(__file__))
    histo_dir = script_dir + "/Output/" + args.histo_dir
    os.makedirs(histo_dir, exist_ok=True)
    print(f"[INFO] Output directory for the merged dataframe and histograms: {histo_dir}")

    if not args.skip_histos:

        ##############################################################
        # Prepare the merged dataframe from NGT input files
        ##############################################################

        path_df = f"{histo_dir}/df_ngt_{tau_reco}.root"

        base_dir_ngt = args.in_dir_sig
        print(f"[INFO] Reading signal NGT root files from {base_dir_ngt}")
        df_sig = merge_hlt(base_dir_ngt, path_df, args)

        base_dir_ngt = args.in_dir_bkg
        print(f"[INFO] Reading background NGT root files from {base_dir_ngt}")
        df_bkg = merge_hlt(base_dir_ngt, path_df, args)

    if not args.skip_histos:

        if tagger == 'tau':
            hlt_collection = "hltHpsPFTau" if tau_reco == "DeepTau" else "hltAK4PuppiJet"
            gen_collection = "GenVisTau"
            match_dR = 0.1 if tau_reco == "DeepTau" else 0.4

            # HLT taus matched to a gen-level hadronic tau
            df_sig = df_sig.Define("hlt_obj_genIdx", f"MatchToGen({hlt_collection}_eta, {hlt_collection}_phi, {gen_collection}_eta, {gen_collection}_phi, {match_dR})")
            df_sig = df_sig.Define("hlt_obj_isSignal", "hlt_obj_genIdx >= 0")

            # HLT taus not matched to any gen-level hadronic tau
            df_bkg = df_bkg.Define("hlt_obj_genIdx", f"MatchToGen({hlt_collection}_eta, {hlt_collection}_phi, {gen_collection}_eta, {gen_collection}_phi, {match_dR})")
            df_bkg = df_bkg.Define("hlt_obj_isBackground", "hlt_obj_genIdx == -1")

        else:  # btag
            hlt_collection = "hltAK4PuppiJet"
            match_dR = 0.4

            # Extract gen b-quark eta/phi (last copies) into transient vectors
            for df_name, df in [("sig", df_sig), ("bkg", df_bkg)]:
                df = df.Define("genb_eta", "RVecF genb_eta; RVecF genb_phi; GetGenBQuarks(GenPart_pdgId, GenPart_genPartIdxMother, genb_eta, genb_phi, GenPart_eta, GenPart_phi); return genb_eta;")
                df = df.Define("genb_phi", "RVecF genb_eta2; RVecF genb_phi2; GetGenBQuarks(GenPart_pdgId, GenPart_genPartIdxMother, genb_eta2, genb_phi2, GenPart_eta, GenPart_phi); return genb_phi2;")
                df = df.Define("hlt_obj_genIdx", f"MatchToGen({hlt_collection}_eta, {hlt_collection}_phi, genb_eta, genb_phi, {match_dR})")
                if df_name == "sig":
                    df = df.Define("hlt_obj_isSignal", "hlt_obj_genIdx >= 0")
                    df_sig = df
                else:
                    df = df.Define("hlt_obj_isBackground", "hlt_obj_genIdx == -1")
                    df_bkg = df

        ##############################################################
        # Save histograms to root file
        ##############################################################

        print(f"[INFO] Saving histograms to {histo_dir}/histos_roc_{mode_label}.root")
        histos_file = ROOT.TFile(f"{histo_dir}/histos_roc_{mode_label}.root", "RECREATE")

        df_sig = df_sig.Define("sig_score", f"{score_name}[hlt_obj_isSignal]")
        histos_sig = df_sig.Histo1D((f"sig_{score_name}_score", f"{score_name};Signal {mode_label} score;Events", bins, min_val, max_val), "sig_score")
        histos_file.WriteObject(histos_sig.GetValue(), f"sig_{score_name}_score")

        df_bkg = df_bkg.Define("bkg_score", f"{score_name}[hlt_obj_isBackground]")
        histos_bkg = df_bkg.Histo1D((f"bkg_{score_name}_score", f"{score_name};Background {mode_label} score;Events", bins, min_val, max_val), "bkg_score")
        histos_file.WriteObject(histos_bkg.GetValue(), f"bkg_{score_name}_score")

        histos_file.Close()

    ##############################################################
    # Plot histograms
    ##############################################################

    plots_dir = script_dir + "/Output/" + args.plots_dir
    os.makedirs(plots_dir, exist_ok=True)
    print(f"[INFO] Output directory for plots: {plots_dir}")

    # Open root file with histograms
    histos_file = ROOT.TFile(f"{histo_dir}/histos_roc_{mode_label}.root", "READ")

    fig, ax1 = plt.subplots(1, figsize=(10,10))                  
    hep.cms.label("Preliminary", data=False, ax=ax1, rlabel="(200 PU) 14 TeV", fontsize=22)

    hist_sig = histos_file.Get(f"sig_{score_name}_score")
    if not hist_sig:
        print(f"[WARNING] Histogram sig_{score_name}_score not found, skipping.")
        sys.exit()
    hist_sig.Scale(1/hist_sig.Integral())

    hist_bkg = histos_file.Get(f"bkg_{score_name}_score")
    if not hist_bkg:
        print(f"[WARNING] Histogram bkg_{score_name}_score not found, skipping.")
        sys.exit()
    hist_bkg.Scale(1/hist_bkg.Integral())

    edges = np.linspace(min_val, max_val, bins + 1)

    sel_color = '#f89c20'
    centers, contents_bkg, errors = hist_to_numpy(hist_bkg)
    hep.histplot(contents_bkg, edges, ax=ax1, color=sel_color, histtype='fill', alpha=0.5)
    hep.histplot(contents_bkg, edges, ax=ax1, color=sel_color, histtype='step')
    ax1.errorbar(centers, contents_bkg, yerr=errors, fmt="o", markersize=3, capsize=2, color=sel_color, label=rf"{bkg_obj_label} (QCD multi-jet)")

    sel_color = '#5790fc'
    centers, contents_sig, errors = hist_to_numpy(hist_sig)
    hep.histplot(contents_sig, edges, ax=ax1, color=sel_color, histtype='fill', alpha=0.5)
    hep.histplot(contents_sig, edges, ax=ax1, color=sel_color, histtype='step')
    ax1.errorbar(centers, contents_sig, yerr=errors, fmt="o", markersize=3, capsize=2, color=sel_color, label=rf"{sig_obj_label} ($HH \rightarrow bb\tau\tau$)")

    ax1.set_xlabel(f"{mode_label} score")
    ax1.set_ylabel("Normalized Events")
    ax1.legend(frameon=False, loc="upper left", fontsize=20, alignment="left") #, title=f"{tau_reco}", title_fontsize=20)
    ax1.set_xlim(min_val, max_val)
    ax1.grid(True, alpha=0.75, linestyle="dashdot", linewidth=0.75)

    out_path = f"{plots_dir}/{mode_label}_score"
    print(f"[INFO] Saving plot: {out_path}")
    fig.savefig(out_path + ".png", dpi=150)
    fig.savefig(out_path + ".pdf", dpi=150)

    ax1.set_yscale('log')
    ax1.set_ylim(1.e-4, 2)

    out_path = f"{plots_dir}/{mode_label}_score_log"
    print(f"[INFO] Saving plot: {out_path}")
    fig.savefig(out_path + ".png", dpi=150)
    fig.savefig(out_path + ".pdf", dpi=150)

    plt.close(fig)

    ##############################################################
    # Plot ROC curve
    ##############################################################

    # contents_sig / contents_bkg are the normalized score distributions.
    # Scan the threshold: efficiency = fraction of taus with score >= threshold.
    sig_eff = np.array([contents_sig[i:].sum() for i in range(bins)])
    bkg_eff = np.array([contents_bkg[i:].sum() for i in range(bins)])

    # Threshold = lower edge of each score bin.
    # Keep the natural increasing-threshold ordering for WP interpolation:
    # sig_eff/bkg_eff decrease monotonically as the threshold increases.
    thresholds = np.linspace(min_val, max_val, bins)
    thr_asc = thresholds
    sig_eff_vs_thr = sig_eff
    bkg_eff_vs_thr = bkg_eff

    # Sort by increasing background efficiency for a clean curve
    order = np.argsort(bkg_eff)
    bkg_eff, sig_eff = bkg_eff[order], sig_eff[order]
    thresholds = thresholds[order]

    # Area under the curve (trapezoidal)
    # np.trapezoid exists only in NumPy >= 2.0; older versions call it np.trapz
    trapezoid = getattr(np, "trapezoid", None) or np.trapz
    auc = trapezoid(sig_eff, bkg_eff)

    fig, ax2 = plt.subplots(1, figsize=(10,10))
    hep.cms.label("Preliminary", data=False, ax=ax2, rlabel="(200 PU) 14 TeV", fontsize=22)

    # Axes inverted: TPR on x, FPR on y (log scale)
    ax2.plot(sig_eff, bkg_eff, "-", color='#9c9ca1', linewidth=2, label=rf"{mode_label} (AUC = {auc:.3f})")
    # ax2.plot([0, 1], [0, 1], "--", color='#9c9ca1', linewidth=1.5, label="Random")

    # Mark the requested score thresholds: show the resulting (TPR, FPR) point.
    # Interpolate TPR/FPR against the increasing score threshold.
    wp_colors = ['#ffa90e', '#3f90da', '#99670a']
    wp_tprs = []
    wp_fprs = []
    for i_wp, thr_wp in enumerate(args.wps):
        tpr_wp = np.interp(thr_wp, thr_asc, sig_eff_vs_thr)
        fpr_wp = np.interp(thr_wp, thr_asc, bkg_eff_vs_thr)
        wp_tprs.append(tpr_wp)
        wp_fprs.append(fpr_wp)
        wp_color = wp_colors[i_wp % len(wp_colors)]
        ax2.plot(tpr_wp, fpr_wp, "o", color=wp_color, markersize=10, markeredgecolor='black', markeredgewidth=1.2, zorder=5)
        ax2.annotate(f"Threshold = {thr_wp:g}\nTPR = {tpr_wp:.3f}\nFPR = {fpr_wp:.3f}", (tpr_wp, fpr_wp),
                     fontweight="bold", textcoords="offset points", xytext=(10, -10), fontsize=14, color=wp_color, va="top")

    ax2.set_xlabel(rf"{sig_obj_label} efficiency (TPR)")
    ax2.set_ylabel(rf"{bkg_obj_label} efficiency (FPR)")
    ax2.set_yscale('log')
    ax2.legend(frameon=False, loc="upper left", fontsize=20, alignment="left")
    # Widen the axes to include the requested working points
    ax2.set_xlim(0, 1)
    ax2.set_ylim(1e-4, 1)
    ax2.grid(True, alpha=0.75, linestyle="dashdot", linewidth=0.75)

    out_path = f"{plots_dir}/{mode_label}_roc"
    print(f"[INFO] Saving plot: {out_path}")
    fig.savefig(out_path + ".png", dpi=150)
    fig.savefig(out_path + ".pdf", dpi=150)
    plt.close(fig)
