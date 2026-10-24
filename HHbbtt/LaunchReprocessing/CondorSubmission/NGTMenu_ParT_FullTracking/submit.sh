#!/bin/bash
OUTPUTDIR="/eos/user/e/evernazz/NanoProdHHbbtt/NGTMenu_ParT_FullTracking/OutNano"
SAMPLE_FILE="GluGluToHHTo2B2Tau_node_SM_TuneCP5_14TeV-madgraph-pythia8.txt"
mkdir -p $OUTPUTDIR
ls -altr
sleep 5
echo "Starting job on " $(date)                    # Date/time of start of job
echo "Running on: $(uname -a)"                     # Condor job is running on this node
echo "System software: $(cat /etc/redhat-release)" # Operating System on the node
export SCRAM_ARCH=el9_amd64_gcc13
source /cvmfs/cms.cern.ch/cmsset_default.sh
sleep 5
echo "Start preparing environment!"
tar -xvf Prod_CMSSW_17_0_0_pre6_52159_52124_52272.tgz # decompress CMSSW tarball
ls -altr
cd CMSSW_17_0_0_pre6/src
scram b ProjectRename       # Set project directory
eval $(scramv1 runtime -sh) # Equivalent to cmsenv
line_number=$(($2 + 1))     # $2 == process number
inputFile=$(sed -n "${line_number}p" $SAMPLE_FILE)
echo "Input file is: $inputFile"
echo "Starting processing"

cmsDriver.py step2 -n -1 \
    -s L1,L1TrackTrigger,L1P2GT,HLT:NGTScouting,NANO:@NGTScoutingVal+@Phase2L1DPG,VALIDATION:@hltValidation \
    --procModifiers nano_l1_hlt --processName HLTX \
    --datatier GEN-SIM-DIGI-RAW-MINIAOD --eventcontent NANOAODSIM \
    --conditions auto:phase2_realistic_T35 --geometry ExtendedRun4D110 --era Phase2C17I13M9 \
    --customise SLHCUpgradeSimulations/Configuration/aging.customise_aging_1000,L1Trigger/Configuration/customisePhase2TTOn110.customisePhase2TTOn110 \
    --filein $inputFile --fileout file:step2.root --python_filename rerun_L1_HLT_NANO_cfg.py \
    --mc --inputCommands='keep *, drop *_hlt*_*_HLT, drop triggerTriggerFilterObjectWithRefs_l1t*_*_HLT, drop *_simEcalUnsuppressedDigis_*_*, drop l1tPFJets_*_*_*, drop l1tTrackerMuons_l1tTkMuonsGmt*_*_HLT' \
    --no_exec

cmsRun -n 10 rerun_L1_HLT_NANO_cfg.py

echo "Begin File Transfer!"
ls -altr
xrdcp step2.root root://eosuser.cern.ch/$OUTPUTDIR/step2_$2.root