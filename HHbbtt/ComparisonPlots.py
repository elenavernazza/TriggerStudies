import matplotlib.pyplot as plt
import mplhep as hep
import sys
plt.style.use(hep.style.CMS)

from Utils import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Arguments for ComparisonPlots.py')
    parser.add_argument('--ref-histo', type=str, default='./Output/Dataframes/histos_acceptance_DeepTau.root', help='Path to root file with reference histogram.')
    parser.add_argument('--ref-histo-name', type=str, default='Ch_tautau/PassHLT/HH_mass', help='Name of the reference histogram.')
    parser.add_argument('--ref-histo-label', type=str, default='HLT acceptance (DeepTau)', help='Label of the reference histogram.')
    parser.add_argument('--tar-histo', type=str, default='./Output/Dataframes/histos_acceptance_ParT.root', help='Path to root file with target histogram.')
    parser.add_argument('--tar-histo-name', type=str, default='Ch_tautau/PassHLT/HH_mass', help='Name of the target histogram.')
    parser.add_argument('--tar-histo-label', type=str, default='HLT acceptance (ParT)', help='Label of the target histogram.')
    parser.add_argument('--all-histo-name', type=str, default='Ch_tautau/All/HH_mass', help='Name of the all events histogram.')
    parser.add_argument('--all-histo-label', type=str, default='All events', help='Label of the all events histogram.')
    parser.add_argument('--plot-name', default='Output/Comparison', help='Path to the output plot.')
    parser.add_argument('--ratio-plot', action='store_true', help='Add ratio plot in the bottom pannel.')
    parser.add_argument('--rebin', type=int, default=1, help='Rebin factor.')
    args = parser.parse_args()

    # Open root file with histograms
    all_histo_file = ROOT.TFile(f"{args.ref_histo}", "READ")
    ref_histo_file = ROOT.TFile(f"{args.ref_histo}", "READ")
    tar_histo_file = ROOT.TFile(f"{args.tar_histo}", "READ")

    all_hist = all_histo_file.Get(f"{args.all_histo_name}")
    ref_hist = ref_histo_file.Get(f"{args.ref_histo_name}")
    tar_hist = tar_histo_file.Get(f"{args.tar_histo_name}")

    rebin = int(args.rebin)
    all_hist = all_hist.Rebin(rebin)
    ref_hist = ref_hist.Rebin(rebin)
    tar_hist = tar_hist.Rebin(rebin)

    if not all_hist:
        print(f"[WARNING] Histogram {args.all_histo_name} not found in {args.ref_histo}, skipping.")
        sys.exit()
    if not ref_hist:
        print(f"[WARNING] Histogram {args.ref_histo_name} not found in {args.ref_histo}, skipping.")
        sys.exit()
    if not tar_hist:
        print(f"[WARNING] Histogram {args.tar_histo_name} not found in {args.tar_histo}, skipping.")
        sys.exit()

    variables_dict = {
        "mass": ["mass [GeV]", r"Mass [GeV]", 40, 200, 1000],
        "pt": ["p_{T} [GeV]", r"$p_{T}$ [GeV]", 40, 0, 400],
        "eta": ["#eta", r"$\eta$", 50, -5, 5],
        "phi": ["#phi", r"$\phi$", 50, -3.14, 3.14]
    }

    obj_labels = {
        "HH": "Gen HH",
        "Hbb": r"Gen $H_{bb}$",
        "Htt": r"Gen $H_{\tau\tau}$",
        "bjet1": r"Gen $b-jet_1$",
        "bjet2": r"Gen $b-jet_2$",
        "ele": r"Gen $e$", 
        "vistau": r"Gen $\tau_{h}$",
        "muon": r"Gen $\mu$",
        "vistau1": r"Gen $\tau_{h,1}$",
        "vistau2": r"Gen $\tau_{h,2}$",
    }

    channels_dict = {
        "etau": r"$\tau_{e}\tau_{h}$", 
        "mutau": r"$\tau_{\mu}\tau_{h}$", 
        "tautau": r"$\tau_{h}\tau_{h}$"
    }

    channel = args.all_histo_name.split("/")[0].split("Ch_")[-1]
    obj = args.all_histo_name.split("/")[-1].split("_")[0]
    var = args.all_histo_name.split("/")[-1].split("_")[1]
    label_latex = obj_labels[obj]

    print(channel, obj, label_latex)

    if args.ratio_plot:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12),  sharex=True, gridspec_kw={"height_ratios": [0.8, 0.2], "hspace": 0.05})
        ax2.set_xlabel(f"{obj_labels[obj]} {variables_dict[var][1]}")
    else:
        fig, ax1 = plt.subplots(1, figsize=(10,10))
        ax1.set_xlabel(f"{obj_labels[obj]} {variables_dict[var][1]}")
        ax2 = ax1.twinx()
        ax2.set_ylabel("Ratio")
        ax2.set_ylim(0, 1.35)

    hep.cms.label("Preliminary", data=False, ax=ax1, rlabel=r"$HH \rightarrow bb\tau\tau$ (200 PU)", fontsize=22)

    edges = np.linspace(variables_dict[var][3], variables_dict[var][4], int(variables_dict[var][2]/rebin) + 1)
    den = max_count = 0
    ref_contents = ref_errors = None

    ######################################
    # Histogram all events
    ######################################
    
    centers, contents, errors = hist_to_numpy(all_hist)
    den = all_hist.GetEntries()
    max_count = np.max(contents)
    ref_contents = contents.copy()
    ref_errors = errors.copy()
    # hep.histplot(contents, edges, ax=ax1, color='#9c9ca1', histtype='fill', alpha=0.5)
    hep.histplot(contents, edges, ax=ax1, color='#9c9ca1', histtype='step')
    ax1.errorbar(centers, contents, yerr=errors, fmt="o", markersize=3, capsize=2, color='#9c9ca1', label=f"{args.all_histo_label}")

    ######################################
    # Reference and Target histograms
    ######################################

    for hist, label, color, zorder in [(ref_hist, args.ref_histo_label, '#7a21dd', 3),
                                       (tar_hist, args.tar_histo_label, '#5790fc', 2)]:

        centers, contents, errors = hist_to_numpy(hist)
        frac = hist.GetEntries() / den * 100
        frac_err = np.sqrt(hist.GetEntries()) / den * 100
        frac_label = rf"= $({frac:.1f}\pm{frac_err:.1f})\%$"
        ratio = np.full_like(contents, np.nan, dtype=float)
        ratio_err = np.full_like(contents, np.nan, dtype=float)
        mask = ref_contents > 5
        ratio[mask] = contents[mask] / ref_contents[mask]
        ratio_err[mask] = np.sqrt(np.clip(ratio[mask] * (1 - ratio[mask]), 0, None) / ref_contents[mask])

        if args.ratio_plot:
            hep.histplot(contents, edges, ax=ax1, color=color, histtype='fill', alpha=0.5, zorder=zorder)
            hep.histplot(contents, edges, ax=ax1, color=color, histtype='step', zorder=zorder)
            ax1.errorbar(centers, contents, yerr=errors, fmt="o", markersize=3, capsize=2, color=color, zorder=zorder, label=f"{label} {frac_label}")
            ax2.errorbar(centers[mask], ratio[mask], yerr=ratio_err[mask], fmt="o--", markersize=3, capsize=2, elinewidth=1, color=color)
            ax2.set_yticks([0.0, 0.5, 1.0])
            ax2.set_ylabel("Ratio")
            ax2.set_ylim(-0.1, 1.1)
            ax2.grid(True, alpha=0.75, linestyle="dashdot", linewidth=0.75)
            ax1.grid(True, alpha=0.75, linestyle="dashdot", linewidth=0.75)

        else:
            # hep.histplot(contents, edges, ax=ax1, color=color, histtype='fill', alpha=0.5, zorder=zorder)
            # hep.histplot(contents, edges, ax=ax1, color=color, histtype='step', zorder=zorder)
            ax1.errorbar([], [], yerr=[], fmt="o", markersize=3, capsize=2, color=color, zorder=zorder, label=f"{label} {frac_label}")
            ax2.errorbar(centers[mask], ratio[mask], yerr=ratio_err[mask], fmt="o--", markersize=3, capsize=2, elinewidth=1, color=color)
            ax1.grid(True, axis="x", alpha=0.75, linestyle="dashdot", linewidth=0.75)
            ax2.grid(True, axis="both", alpha=0.75, linestyle="dashdot", linewidth=0.75)

    ax1.set_ylabel("Events")
    ax1.legend(frameon=False, loc="upper left", title=f"Channel {channels_dict[channel]}", title_fontsize=18, fontsize=18, alignment="left")
    ax1.set_xlim(variables_dict[var][3], variables_dict[var][4])
    ax1.set_ylim(0,1.35*max_count)

    plot_name = f"{args.plot_name}_ratio" if args.ratio_plot else f"{args.plot_name}"
    plot_dir = plot_name.rsplit("/", 1)[0] if "/" in plot_name else "./"
    os.makedirs(plot_dir, exist_ok=True)

    print(f"[INFO] Saving plot: {plot_name}")
    fig.savefig(plot_name + ".png", dpi=150)
    fig.savefig(plot_name + ".pdf", dpi=150)
    plt.close(fig)
