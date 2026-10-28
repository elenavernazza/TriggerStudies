import matplotlib.pyplot as plt
import mplhep as hep
plt.style.use(hep.style.CMS)

from Utils import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Arguments for ComparisonRocCurve.py')
    parser.add_argument('--ref-histo', type=str, default='./Output/Dataframes/histos_roc_DeepTau.root', help='Path to root file with reference (DeepTau) histograms.')
    parser.add_argument('--ref-histo-label', type=str, default='DeepTau', help='Label of the reference curve.')
    parser.add_argument('--tar-histo', type=str, default='./Output/Dataframes/histos_roc_ParT.root', help='Path to root file with target (ParT) histograms.')
    parser.add_argument('--tar-histo-label', type=str, default='ParT', help='Label of the target curve.')
    parser.add_argument('--plot-name', default='Output/Plots_RocCurve/ROC_DeepTau_ParT', help='Path to the output plot.')
    parser.add_argument('--fpr-wp', type=float, default=0.20, help='Fixed fake-rate (FPR) working point to mark.')
    parser.add_argument('--bins', type=int, default=50, help='Number of bins used in the score histograms.')
    parser.add_argument('--min-val', type=float, default=0.0, help='Minimum score value.')
    parser.add_argument('--max-val', type=float, default=1.0, help='Maximum score value.')
    args = parser.parse_args()

    # np.trapezoid exists only in NumPy >= 2.0; older versions call it np.trapz
    trapezoid = getattr(np, "trapezoid", None) or np.trapz

    def build_roc(path, sig_key, bkg_key):
        """Return (bkg_eff, sig_eff, auc) from a histos_roc file, or None if missing."""
        f = ROOT.TFile.Open(path, "READ")
        if not f or f.IsZombie():
            print(f"[WARNING] Cannot open {path}, skipping.")
            return None
        hist_sig = f.Get(sig_key)
        hist_bkg = f.Get(bkg_key)
        if not hist_sig or not hist_bkg:
            print(f"[WARNING] Histograms {sig_key}/{bkg_key} not found in {path}, skipping.")
            f.Close()
            return None
        # Detach from the file so the histograms survive after f.Close()
        hist_sig = hist_sig.Clone("hist_sig_clone")
        hist_bkg = hist_bkg.Clone("hist_bkg_clone")
        hist_sig.SetDirectory(0)
        hist_bkg.SetDirectory(0)
        f.Close()
        hist_sig.Scale(1 / hist_sig.Integral())
        hist_bkg.Scale(1 / hist_bkg.Integral())
        _, contents_sig, _ = hist_to_numpy(hist_sig)
        _, contents_bkg, _ = hist_to_numpy(hist_bkg)
        # Threshold = lower edge of each score bin
        thresholds = np.linspace(args.min_val, args.max_val, args.bins)
        sig_eff = np.array([contents_sig[i:].sum() for i in range(args.bins)])
        bkg_eff = np.array([contents_bkg[i:].sum() for i in range(args.bins)])
        order = np.argsort(bkg_eff)
        bkg_eff, sig_eff = bkg_eff[order], sig_eff[order]
        thresholds = thresholds[order]
        auc = trapezoid(sig_eff, bkg_eff)
        return bkg_eff, sig_eff, thresholds, auc

    def wp_at_fpr(bkg_eff, sig_eff, thresholds, fpr):
        """Interpolated TPR and score threshold at exactly the target FPR."""
        # bkg_eff is sorted ascending; np.interp requires increasing x
        tpr = np.interp(fpr, bkg_eff, sig_eff)
        thr = np.interp(fpr, bkg_eff, thresholds)
        return fpr, tpr, thr

    curves = [
        (args.ref_histo, args.ref_histo_label, '#7a21dd'),
        (args.tar_histo, args.tar_histo_label, '#5790fc'),
    ]

    fig, ax = plt.subplots(1, figsize=(10, 10))
    hep.cms.label("Preliminary", data=False, ax=ax, rlabel=r"$HH \rightarrow bb\tau\tau$ (200 PU) 14 TeV", fontsize=22)

    # Stagger the WP annotations vertically to avoid overlap
    wp_offsets = [(5, 10), (-10, -20)]
    vas = ["bottom", "top"]
    has = ["right", "left"]
    for i_curve, (path, label, color) in enumerate(curves):
        score_name = "hltHpsPFTau_deepTauVSjet" if label == "DeepTau" else "hltAK4PuppiJet_ParT_TauvsAll"
        roc = build_roc(path, f"sig_{score_name}_score", f"bkg_{score_name}_score")
        if roc is None:
            continue
        bkg_eff, sig_eff, thresholds, auc = roc
        # Axes inverted: TPR on x, FPR on y (log scale)
        ax.plot(sig_eff, bkg_eff, "-", color=color, linewidth=2, label=rf"{label} (AUC = {auc:.3f})")

        # Mark the working point at the fixed FPR
        wp_fpr, wp_tpr, wp_thr = wp_at_fpr(bkg_eff, sig_eff, thresholds, args.fpr_wp)
        ax.plot(wp_tpr, wp_fpr, "o", color=color, markersize=10, markeredgecolor='black', markeredgewidth=1.2, zorder=5)
        off = wp_offsets[i_curve % len(wp_offsets)]
        va = vas[i_curve % len(wp_offsets)]
        ha = has[i_curve % len(wp_offsets)]
        ax.annotate(f"Threshold = {wp_thr:.3f}\nTPR = {wp_tpr:.3f}", (wp_tpr, wp_fpr), textcoords="offset points",
                    fontweight="bold", xytext=off, fontsize=14, color=color, ha=ha, va=va)

    # Horizontal line at the fixed FPR
    ax.axhline(args.fpr_wp, color='#9c9ca1', linestyle="dashdot", linewidth=1.5)
    # x in axes-fraction coords (stays visible regardless of xlim); y in data coords
    ax.text(0.02, args.fpr_wp * 0.85, f"FPR = {args.fpr_wp:.0%}", color='#5c5c5e', fontsize=15,
            ha="left", va="top", transform=ax.get_yaxis_transform())

    # ax.plot([0, 1], [0, 1], "--", color='#9c9ca1', linewidth=1.5, label="Random")

    ax.set_xlabel(r"Genuine $\tau_h$ efficiency (TPR)")
    ax.set_ylabel(r"Fake $\tau_h$ efficiency (FPR)")
    ax.set_yscale('log')
    ax.legend(frameon=False, loc="upper left", fontsize=20, alignment="left")
    ax.set_xlim(0.5, 1)
    ax.set_ylim(1e-3, 1)
    ax.grid(True, alpha=0.75, linestyle="dashdot", linewidth=0.75)

    plot_name = args.plot_name + f"_FPR{args.fpr_wp}"
    plot_dir = plot_name.rsplit("/", 1)[0] if "/" in plot_name else "./"
    os.makedirs(plot_dir, exist_ok=True)

    print(f"[INFO] Saving plot: {plot_name}")
    fig.savefig(plot_name + ".png", dpi=150)
    fig.savefig(plot_name + ".pdf", dpi=150)
    plt.close(fig)
