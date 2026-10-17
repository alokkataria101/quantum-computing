"""Restricted Hartree-Fock energy of H2 at 0.74 Å (STO-3G) with PySCF."""
from pyscf import gto, scf

# Define the molecule
mol = gto.M(
    atom = '''
    H 0 0 0
    H 0 0 0.74
    ''',
    basis = 'sto-3g'
)

# Run Hartree-Fock calculation
mf = scf.RHF(mol)

energy = mf.kernel()

print("Ground state energy (Hartree):", energy)
