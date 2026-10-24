# Prod_CMSSW_17_0_0_pre6

In a clean environment, create a folder that will contain the CMSSW version with your own configuration.

1. Get the CMSSW release where your developments are available:
```
mkdir Prod_CMSSW_17_0_0_pre6
cd Prod_CMSSW_17_0_0_pre6
cmsrel CMSSW_17_0_0_pre6
cd CMSSW_17_0_0_pre6/src && cmsenv && git cms-init
```
2. Add your developments and compile:
```
scram b -j
```
3. Copy the list of input files inside the $CMSSW_BASE/src folder:
```
cp <path_to>/GluGluToHHTo2B2Tau_node_SM_TuneCP5_14TeV-madgraph-pythia8.txt .
```
4. Compress:
```
cd ../../
tar -czvf Prod_CMSSW_17_0_0_pre6.tgz CMSSW_17_0_0_pre6
```

# Prod_CMSSW_17_0_0_pre6_52159

In a clean environment, create a folder that will contain the CMSSW version with your own configuration.

1. Get the CMSSW release where your developments are available:
```
mkdir Prod_CMSSW_17_0_0_pre6_52159
cd Prod_CMSSW_17_0_0_pre6_52159
cmsrel CMSSW_17_0_0_pre6
cd CMSSW_17_0_0_pre6/src && cmsenv && git cms-init
```
2. Add your developments (e.g. PR-52159) and compile:
```
# git cms-rebase-topic 52159
git cms-remote add cms-ngt-hlt
git fetch cms-ngt-hlt
git cms-addpkg CommonTools/RecoAlgos Configuration/EventContent Geometry/CommonTopologies \
 HLTrigger/Configuration HLTrigger/NGTScouting RecoLocalTracker/SiPixelClusterizer \
 RecoLocalTracker/SiPixelRecHits RecoTracker/Configuration RecoTracker/FinalTrackSelectors \
 RecoTracker/PixelSeeding RecoTracker/PixelTrackFitting Validation/RecoTrack Validation/RecoVertex
git cherry-pick 67b35e7ce036408c43306fcf09f4a0cc37a73c86^..5c939ffc9b5cb0e10c5ef669a65f4ae724746f1a
scram b -j
```
3. Copy the list of input files inside the $CMSSW_BASE/src folder:
```
cp <path_to>/GluGluToHHTo2B2Tau_node_SM_TuneCP5_14TeV-madgraph-pythia8.txt .
```
4. Compress:
```
cd ../../
tar -czvf Prod_CMSSW_17_0_0_pre6_52159.tgz CMSSW_17_0_0_pre6
```

# Prod_CMSSW_17_0_0_pre6_52159_52124_52272

In a clean environment, create a folder that will contain the CMSSW version with your own configuration.

1. Get the CMSSW release where your developments are available:
```
mkdir Prod_CMSSW_17_0_0_pre6_52159_52124_52272
cd Prod_CMSSW_17_0_0_pre6_52159_52124_52272
cmsrel CMSSW_17_0_0_pre6
cd CMSSW_17_0_0_pre6/src && cmsenv && git cms-init
```
2. Add your developments (e.g. PR-52159) and compile:
```
# git cms-rebase-topic 52159
git cms-remote add cms-ngt-hlt
git fetch cms-ngt-hlt
git cms-addpkg CommonTools/RecoAlgos Configuration/EventContent Geometry/CommonTopologies \
 HLTrigger/Configuration HLTrigger/NGTScouting RecoLocalTracker/SiPixelClusterizer \
 RecoLocalTracker/SiPixelRecHits RecoTracker/Configuration RecoTracker/FinalTrackSelectors \
 RecoTracker/PixelSeeding RecoTracker/PixelTrackFitting Validation/RecoTrack Validation/RecoVertex
git cherry-pick 67b35e7ce036408c43306fcf09f4a0cc37a73c86^..5c939ffc9b5cb0e10c5ef669a65f4ae724746f1a
# git cms-rebase-topic 52124
git cms-remote add mmusich
git fetch mmusich
git cms-addpkg RecoBTag/Combined RecoBTag/ONNXRuntime 
git cherry-pick 42f175b1aaddd8032f5d7393ed45a66154fbf06d^..824ee01dc303f0fed5f69497ae4652c13560117a
# git cms-rebase-topic 52272
git cherry-pick 223842f7d30f8d291b3919a6457873af886ac90d^..223842f7d30f8d291b3919a6457873af886ac90d
scram b -j
```
3. Copy the list of input files inside the $CMSSW_BASE/src folder:
```
cp <path_to>/GluGluToHHTo2B2Tau_node_SM_TuneCP5_14TeV-madgraph-pythia8.txt .
```
4. Compress:
```
cd ../../
tar -czvf Prod_CMSSW_17_0_0_pre6_52159_52124_52272.tgz CMSSW_17_0_0_pre6
```