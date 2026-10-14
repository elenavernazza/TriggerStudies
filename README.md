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
voms-proxy-init -voms cms -rfc -valid 192:00
python3 RunAll.py --menu HLT --start-from 0 --n-files 10 --out-dir DeepTau # --dry-run 1
python3 RunAll.py --menu NGT --start-from 0 --n-files 10 --out-dir DeepTau # --dry-run 1
```

### 2. Set-up the new developments (ParT)
Get the PR with the new ParT reconstruction sequence:
```
cd $CMSSW_BASE/src
git switch -c NGTtracking_ParT
git cms-rebase-topic 52124
scram b -j
```
Run the reprocessing for HLT and NGT Scouting menus:
```
cd TriggerStudies/HHbbtt/LaunchReprocessing
python3 RunAll.py --menu NGT --start-from 0 --n-files 10 --out-dir ParT  # --dry-run 1
```

### 3. Run the trigger acceptance comparison
```
cd ..
python3 CompareAcceptance.py --tau-hlt-trig DeepTau # --max-files 2 --skip-mergin --skip-histos
python3 CompareAcceptance.py --tau-hlt-trig ParT # --max-files 2 --skip-mergin --skip-histos
```