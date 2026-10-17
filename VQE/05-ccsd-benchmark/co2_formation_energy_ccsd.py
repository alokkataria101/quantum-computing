"""Reaction energy of  C (atom) + O2 -> CO2  with CCSD/cc-pVDZ (classical benchmark).

CCSD (coupled cluster singles and doubles) is the classical "gold standard" that VQE
results on larger molecules are compared against. Open-shell species use UHF references.

Sign convention: Delta E = E(products) - E(reactants) = E(CO2) - E(C) - E(O2).
A negative value means the reaction releases energy. (The earlier version of this script
computed reactants - products and printed +10.76 eV for this exothermic reaction.)

Experimental reference: Delta H(298 K) = -393.5 - 716.7 = -1110.2 kJ/mol = -11.5 eV.
Electronic energy only here (no zero-point / thermal terms) in a modest basis, so the
result is expected to be somewhat smaller in magnitude.
"""
from pyscf import gto, scf, cc

HARTREE_TO_EV = 27.2114


def compute_ccsd_energy(atom_string, spin, charge=0, basis="cc-pvdz"):
    """Total CCSD energy (Hartree). spin = N_alpha - N_beta."""
    mol = gto.M(
        atom=atom_string,
        basis=basis,
        spin=spin,
        charge=charge,
        unit="Angstrom",
        verbose=0,
    )

    # Hartree-Fock reference
    mf = scf.RHF(mol) if spin == 0 else scf.UHF(mol)
    mf.kernel()

    # CCSD
    mycc = cc.CCSD(mf)
    mycc.kernel()

    return mycc.e_tot


if __name__ == "__main__":
    # Carbon atom (triplet ground state)
    E_C = compute_ccsd_energy("C 0 0 0", spin=2)

    # O2 (triplet ground state)
    E_O2 = compute_ccsd_energy("O 0 0 0; O 0 0 1.21", spin=2)

    # CO2 (singlet, linear)
    E_CO2 = compute_ccsd_energy("C 0 0 0; O 0 0 1.16; O 0 0 -1.16", spin=0)

    delta_hartree = E_CO2 - (E_C + E_O2)
    delta_eV = delta_hartree * HARTREE_TO_EV

    print(f"E(C)   = {E_C:.6f} Ha")
    print(f"E(O2)  = {E_O2:.6f} Ha")
    print(f"E(CO2) = {E_CO2:.6f} Ha")
    print("Reaction Energy (Hartree):", delta_hartree)
    print("Reaction Energy (eV):", delta_eV)
    print("Experimental reference ≈ -11.5 eV")
