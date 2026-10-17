"""Restricted Hartree-Fock energy of water (6-31G basis) with PySCF.

Geometry in Å: O at the origin, H atoms at (0, ±0.757, 0.587) -> O-H ≈ 0.96 Å, H-O-H ≈ 105°.
"""
from pyscf import gto, scf

mol = gto.M(
    atom = '''
    O 0 0 0
    H 0 -0.757 0.587
    H 0 0.757 0.587
    ''',
    basis='6-31g'
)

mf = scf.RHF(mol)
energy = mf.kernel()

print("Water molecule energy:", energy)
