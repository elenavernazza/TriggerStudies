import os, argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Arguments for RunAll.py')
    parser.add_argument('--menu', type=str, choices=['HLT', 'NGT', 'NGTFullTrack'], default='HLT', help='Menu to run (default: %(default)s).')
    parser.add_argument('--start-from', type=int, default=-1, help='Start number (Default: 0)')
    parser.add_argument('--n-files', type=int, default=None, help='Number of files to process (Default: all)')
    parser.add_argument('--n-events', type=int, default=None, help='Number of events per file to process (Default: all)')
    parser.add_argument('--n-threads', type=int, default=0, help='Number of threads (Default: 0)')
    parser.add_argument('--dry-run', type=bool, default=False, help='Only print configuration, without running (Default: false)')
    parser.add_argument('--out-dir', type=str, default='./', help='Output directory (Default: ./)')
    args = parser.parse_args()

    InFileList = 'GluGluToHHTo2B2Tau_node_SM_TuneCP5_14TeV-madgraph-pythia8.txt'
    with open(InFileList, "r") as f:
        in_files = f.readlines()

    n_ev = args.n_events
    start_from = args.start_from if args.start_from is not None else 0
    n_files = args.n_files if args.n_files is not None else len(in_files)
    n_threads = args.n_threads

    if args.menu == "HLT":
        out_dir = args.out_dir + 'HLTMenu'
        print(f"[INFO] Running re-processing with standard HLT menu, output in {out_dir}")
        os.makedirs(out_dir, exist_ok=True)
        for i, i_line in enumerate(in_files[start_from:start_from+n_files]):
            i_file = i_line.strip()
            os.system("aklog") # for tmux surviving
            cmd1 = f"\
        cmsDriver.py step2 -n {n_ev} --nThreads {n_threads} \
        -s L1,L1TrackTrigger,L1P2GT,HLT:75e33,NANO:@Phase2HLTVal+@Phase2L1DPG,VALIDATION:@hltValidation \
        --procModifiers nano_l1_hlt --processName HLTX \
        --datatier GEN-SIM-DIGI-RAW-MINIAOD --eventcontent NANOAODSIM \
        --conditions auto:phase2_realistic_T35 --geometry ExtendedRun4D110 --era Phase2C17I13M9 \
        --customise SLHCUpgradeSimulations/Configuration/aging.customise_aging_1000,L1Trigger/Configuration/customisePhase2TTOn110.customisePhase2TTOn110 \
        --filein {i_file} --fileout file:step2.root --python_filename rerun_L1_HLT_NANO_cfg.py \
        --mc --inputCommands='keep *, drop *_hlt*_*_HLT, drop triggerTriggerFilterObjectWithRefs_l1t*_*_HLT, drop *_simEcalUnsuppressedDigis_*_*, drop l1tPFJets_*_*_*, drop l1tTrackerMuons_l1tTkMuonsGmt*_*_HLT' \
        &> log.log   "
            cmd2 = f"mv step2.root {out_dir}/step2_{i+start_from}.root"
            print(cmd1+'\n'+cmd2)
            
            if not args.dry_run:
                os.system(cmd1)
                os.system(cmd2)

    elif args.menu == "NGT":
        out_dir = args.out_dir + 'NGTMenu'
        print(f"[INFO] Running re-processing with NGT Scouting menu, output in {out_dir}")
        os.makedirs(out_dir, exist_ok=True)
        for i, i_line in enumerate(in_files[start_from:start_from+n_files]):
            i_file = i_line.strip()
            os.system("aklog") # for tmux surviving
            cmd1 = f"\
        cmsDriver.py step2 -n {n_ev} --nThreads {n_threads} \
        -s L1,L1TrackTrigger,L1P2GT,HLT:NGTScouting,NANO:@NGTScoutingVal+@Phase2L1DPG,VALIDATION:@hltValidation \
        --procModifiers nano_l1_hlt,ngtScouting --processName HLTX \
        --datatier GEN-SIM-DIGI-RAW-MINIAOD --eventcontent NANOAODSIM \
        --conditions auto:phase2_realistic_T35 --geometry ExtendedRun4D110 --era Phase2C17I13M9 \
        --customise SLHCUpgradeSimulations/Configuration/aging.customise_aging_1000,L1Trigger/Configuration/customisePhase2TTOn110.customisePhase2TTOn110 \
        --filein {i_file} --fileout file:step2.root --python_filename rerun_L1_NGT_NANO_cfg.py \
        --mc --inputCommands='keep *, drop *_hlt*_*_HLT, drop triggerTriggerFilterObjectWithRefs_l1t*_*_HLT, drop *_simEcalUnsuppressedDigis_*_*, drop l1tPFJets_*_*_*, drop l1tTrackerMuons_l1tTkMuonsGmt*_*_HLT' \
        &> log.log   "
            cmd2 = f"mv step2.root {out_dir}/step2_{i+start_from}.root"
            print(cmd1+'\n'+cmd2)
            
            if not args.dry_run:
                os.system(cmd1)
                os.system(cmd2)

    elif args.menu == "NGTFullTrack":
        out_dir = args.out_dir + 'NGTFullTrackMenu'
        print(f"[INFO] Running re-processing with NGT Scouting menu, output in {out_dir}")
        os.makedirs(out_dir, exist_ok=True)
        for i, i_line in enumerate(in_files[start_from:start_from+n_files]):
            i_file = i_line.strip()
            os.system("aklog") # for tmux surviving
            cmd1 = f"\
        cmsDriver.py step2 -n {n_ev} --nThreads {n_threads} \
        -s L1,L1TrackTrigger,L1P2GT,HLT:NGTScouting,NANO:@NGTScoutingVal+@Phase2L1DPG,VALIDATION:@hltValidation \
        --procModifiers nano_l1_hlt --processName HLTX \
        --datatier GEN-SIM-DIGI-RAW-MINIAOD --eventcontent NANOAODSIM \
        --conditions auto:phase2_realistic_T35 --geometry ExtendedRun4D110 --era Phase2C17I13M9 \
        --customise SLHCUpgradeSimulations/Configuration/aging.customise_aging_1000,L1Trigger/Configuration/customisePhase2TTOn110.customisePhase2TTOn110 \
        --filein {i_file} --fileout file:step2.root --python_filename rerun_L1_NGT_NANO_cfg.py \
        --mc --inputCommands='keep *, drop *_hlt*_*_HLT, drop triggerTriggerFilterObjectWithRefs_l1t*_*_HLT, drop *_simEcalUnsuppressedDigis_*_*, drop l1tPFJets_*_*_*, drop l1tTrackerMuons_l1tTkMuonsGmt*_*_HLT' \
        &> log.log   "
            cmd2 = f"mv step2.root {out_dir}/step2_{i+start_from}.root"
            print(cmd1+'\n'+cmd2)
            
            if not args.dry_run:
                os.system(cmd1)
                os.system(cmd2)
