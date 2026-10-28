#include <vector>
#include <cmath>
#include <algorithm>
#include <ROOT/RVec.hxx>
#include <Math/Vector4D.h>         

using ROOT::RVecF;
using ROOT::RVecI;
using RVecUC = ROOT::VecOps::RVec<unsigned char>;
using RVecS = ROOT::VecOps::RVec<Short_t>;

using ROOT::Math::PtEtaPhiMVector; 

// Returns a vector of size 2 that contains the two indices of the Higgs's coming from the HH decay
RVecI Get_HH_idxs (const RVecI& pdgId, const RVecI& statusFlags)
{
    RVecI HH_idxs;

    for (std::size_t i = 0; i < pdgId.size(); i++) {
        if (!(statusFlags[i] & (1 << 13))) continue; // Final state
        if (pdgId[i] != 25) continue; // Higgs boson
        HH_idxs.push_back(i);
    }
    
    if (HH_idxs.size() != 2) {
        return {-1, -1};
    }
    return HH_idxs;
}

// Follows a particle down its self-copy chain (e.g. tau -> tau -> tau) and
// returns the index of the last copy, i.e. the one that actually decays.
int Get_last_copy(int idx, const RVecI& pdgId, const RVecI& genPartIdxMother)
{
    if (idx < 0) return -1;

    int current = idx;
    int current_pdg = std::abs(pdgId[idx]);
    bool found_next = true;
    while (found_next) {
        found_next = false;
        for (std::size_t i = 0; i < pdgId.size(); i++) {
            if (genPartIdxMother[i] != current) continue;
            if (std::abs(pdgId[i]) == current_pdg) { // self-copy, keep walking
                current = i;
                found_next = true;
                break;
            }
        }
    }
    return current;
}

// Returns the indices of the two Higgs decay products.
// Each index is the LAST copy of the daughter in the GenPart chain
// (self-copies from showering are followed down to the decaying particle).
RVecI Get_H_decay_idxs (int H_idx, const RVecI& pdgId, const RVecI& statusFlags, const RVecI& genPartIdxMother)
{

    RVecI decay_idxs;

    if (H_idx < 0) return {-1, -1};

    for (std::size_t i = 0; i < pdgId.size(); i++) {
        if (genPartIdxMother[i] != H_idx) continue;
        decay_idxs.push_back(Get_last_copy(i, pdgId, genPartIdxMother));
    }

    if (decay_idxs.size() != 2) {
        return {-1, -1};
    }
    return decay_idxs;


}

// Returns the p4 of a di-object
PtEtaPhiMVector Get_diObject_P4(float pt1, float eta1, float phi1, float mass1, float pt2, float eta2, float phi2, float mass2)
{
    PtEtaPhiMVector p4_1(pt1, eta1, phi1, mass1);
    PtEtaPhiMVector p4_2(pt2, eta2, phi2, mass2);
    PtEtaPhiMVector p4_sum = p4_1 + p4_2;
    return p4_sum;
}

// Sorts a vector according to a variable
RVecI Sort_idxs(const RVecI& idxs, const RVecF& var_high)
{
    RVecI sorted = idxs;
    std::sort(sorted.begin(), sorted.end(), [&](int a, int b) {
        float var_a = (a >= 0) ? var_high[a] : -1.f;
        float var_b = (b >= 0) ? var_high[b] : -1.f;
        return var_a > var_b;
    });
    return sorted;
}

// Returns the decay mode of a tau and the index of the visible decay product:
//  {0, idx} for tau -> e, {1, idx} for tau -> mu, {2, idx} for tau -> had
// tau_idx must be the LAST copy of the tau (as returned by Get_H_decay_idxs).
RVecI Get_tau_decay(int tau_idx, const RVecI& pdgId, const RVecI& statusFlags, const RVecI& genPartIdxMother)
{
    if (tau_idx < 0) return {-1, -1};

    for (std::size_t i = 0; i < pdgId.size(); i++) {
        if (genPartIdxMother[i] != tau_idx) continue;
        int abs_pdg = std::abs(pdgId[i]);
        if (abs_pdg == 11) return {0, static_cast<int>(i)}; // tau -> e
        if (abs_pdg == 13) return {1, static_cast<int>(i)}; // tau -> mu
    }

    return {2, tau_idx}; // tau -> h
}

// Returns the index of the collection object closest to the target within a max DeltaR
int GetClosestIdx(float target_eta, float target_phi, RVecF& collection_eta, RVecF& collection_phi, float maxDR) 
{
    float min_dR2 = maxDR * maxDR;
    int closestIdx = -1;

    for (std::size_t i = 0; i < collection_eta.size(); i++) {
        float dEta = collection_eta[i] - target_eta;
        float dPhi = std::abs(collection_phi[i] - target_phi);
        if (dPhi > M_PI) dPhi = 2.0 * M_PI - dPhi;

        float dR2 = dEta * dEta + dPhi * dPhi;
        if (dR2 < min_dR2) {
            min_dR2 = dR2;
            closestIdx = i;
        }
    }

    return closestIdx;

}

// Returns the index of the GenVisTau collection associated to the genTau
int GetGenVisTau(int tau_idx, RVecS& GenVisTau_genPartIdxMother)
{
    for (std::size_t i = 0; i < GenVisTau_genPartIdxMother.size(); i++) {
        if (GenVisTau_genPartIdxMother[i] == tau_idx) {
            return i;
        }
    }
    return -1;
}

// Returns threshold for DeepTau as a function of the tau Pt
float GetDeepTauThr(float pt) {
    float t1 = 0.649, t2 = 0.441, t3 = 0.05, x1 = 35, x2 = 100, x3 = 300; 
    if (pt <= x1) return t1; 
    if (pt >= x3) return t3; 
    if (pt < x2) return (t2 - t1) / (x2 - x1) * (pt - x1) + t1; 
    return (t3 - t2) / (x3 - x2) * (pt - x2) + t2;
}

// Returns threshold for ParT flat in tau Pt
float GetParTThr(float pt) {
    return 0.333;
}

// Returns for each HLT tau the index of the closest GenVisTau within maxDR (-1 if none)
RVecI MatchToGen(const RVecF& hlt_eta, const RVecF& hlt_phi, const RVecF& gen_eta, const RVecF& gen_phi, float maxDR) {

    RVecI matches(hlt_eta.size(), -1);

    for (std::size_t i = 0; i < hlt_eta.size(); i++) {

        float min_dR2 = maxDR * maxDR;

        for (std::size_t j = 0; j < gen_eta.size(); j++) {

            float dEta = gen_eta[j] - hlt_eta[i];
            float dPhi = std::abs(gen_phi[j] - hlt_phi[i]);
            if (dPhi > M_PI) dPhi = 2.0 * M_PI - dPhi;

            float dR2 = dEta*dEta + dPhi*dPhi;
            if (dR2 < min_dR2) { 
                min_dR2 = dR2; 
                matches[i] = j; 
            }
        }
    }
    return matches;
}

// Returns the eta/phi of gen b-quarks (|pdgId| = 5, followed to their last copy)
void GetGenBQuarks(const RVecI& pdgId, const RVecI& genPartIdxMother, RVecF& out_eta, RVecF& out_phi,
                   const RVecF& GenPart_eta, const RVecF& GenPart_phi) {

    out_eta.clear();
    out_phi.clear();

    for (std::size_t i = 0; i < pdgId.size(); i++) {
        if (std::abs(pdgId[i]) != 5) continue;
        int last = Get_last_copy(i, pdgId, genPartIdxMother);
        out_eta.push_back(GenPart_eta[last]);
        out_phi.push_back(GenPart_phi[last]);
    }
}