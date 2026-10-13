# TriggerStudies

## $HH \rightarrow bb\tau\tau$ trigger studies

### 1. Set-up the default (DeepTau)
Get a CMSSW environment compatible with Spring24 MC campaign:
```
cmsrel CMSSW_17_0_0_pre6
cd CMSSW_17_0_0_pre6/src
cmsenv
git cms-init
git switch -c NGTtracking # [OPTIONAL]
git cms-rebase-topic 52159 # [OPTIONAL: improvements in track reconstruction]
scram b -j
```
Install the repository:
```
git clone git@github.com:elenavernazza/TriggerStudies.git
```
Run the reprocessing for HLT and NGT Scouting menus:
```
cd TriggerStudies/HHbbtt/LaunchReprocessing
python3 RunAll.py --menu HLT --start-from 0 --n-files 10 # --dry-run 1
python3 RunAll.py --menu NGT --start-from 0 --n-files 10 # --dry-run 1
```

### 2. Set-up the new developments (ParT)
Get the PR with the new ParT reconstruction sequence
```
git switch -c NGTtracking_ParT
git cms-rebase-topic 52124
scram b -j
```
Run the reprocessing for HLT and NGT Scouting menus:
```
cd TriggerStudies/HHbbtt/LaunchReprocessing
python3 RunAll.py --menu NGT --start-from 0 --n-files 10 # --dry-run 1
```

### 3. Run the trigger acceptance comparison
```
python3 CompareAcceptance.py --max-files 10
```