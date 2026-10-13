#include <vector>
#include <cmath>
#include <algorithm>
#include <ROOT/RVec.hxx>
#include <Math/Vector4D.h>         

using ROOT::RVecF;
using ROOT::RVecI;
using RVecUC = ROOT::VecOps::RVec<unsigned char>;

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

// Returns the indeces of the two Higgs bosons
RVecI Get_H_decay_idxs (int H_idx, const RVecI& pdgId, const RVecI& statusFlags, const RVecI& genPartIdxMother)
{

    RVecI decay_idxs;

    if (H_idx < 0) return {-1, -1};

    for (std::size_t i = 0; i < pdgId.size(); i++) {
        if (genPartIdxMother[i] != H_idx) continue;
        decay_idxs.push_back(i);
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
RVecI Get_tau_decay(int tau_idx, const RVecI& pdgId, const RVecI& statusFlags, const RVecI& genPartIdxMother)
{
    if (tau_idx < 0) return {-1, -1};

    int current = tau_idx;
    bool found_next = true;
    while (found_next) {
        found_next = false;
        for (std::size_t i = 0; i < pdgId.size(); i++) {
            if (genPartIdxMother[i] != current) continue;
            if (std::abs(pdgId[i]) == 15) { // tau self-copy, keep walking
                current = i;
                found_next = true;
                break;
            }
        }
    }

    for (std::size_t i = 0; i < pdgId.size(); i++) {
        if (genPartIdxMother[i] != current) continue;
        int abs_pdg = std::abs(pdgId[i]);
        if (abs_pdg == 11) return {0, static_cast<int>(i)}; // tau -> e
        if (abs_pdg == 13) return {1, static_cast<int>(i)}; // tau -> mu
    }

    return {2, tau_idx}; // tau -> h
}
