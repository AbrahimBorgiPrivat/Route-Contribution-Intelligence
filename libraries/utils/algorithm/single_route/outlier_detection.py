from typing import Set, Dict, FrozenSet
from tqdm import tqdm

def detect_outliers(C2: Dict[FrozenSet[int], float], z: float) -> Set[FrozenSet[int]]:
    """
    Identificerer økonomisk signifikante outlier-delmængder.
    ----------
    Parameters
    ----------
    C2 : Opslagstabel med dækningsgradstab for alle evaluerede delmængder S. (Fx {frozenset({1,2}): -50.0, frozenset({3}): 25.0, ...})
    z  : Tærskelværdi for, hvornår en ændring anses som signifikant forbedring.(Fx 0.0)
    
    -------
    Returns
    -------
    Mængden af alle delmængder S, der opfylder outlier-kriteriet - C2(S) > z  og  ∃ S' ⊃ S : C2(S') < z
    """
    S_sig = set()
    coverage_change = {}
    # Sortér alle sæt efter størrelse (|S|) for at kunne sammenligne korrekt
    subsets = sorted(C2.keys(), key=len)
    size_groups = {}
    for S in subsets:
        size_groups.setdefault(len(S), []).append(S)
    max_size = max(size_groups)
    # Gennemgå alle sæt grupperet efter størrelse
    for k in tqdm(range(max_size), desc="Detecting outliers by size", position=0, leave=False):
        for S in size_groups.get(k, []):
            if C2[S] > z:  
                # Undersøg om en større delmængde med lavere C2 findes
                for larger_k in range(k + 1, max_size + 1):
                    for S2 in size_groups.get(larger_k, []):
                        if S.issubset(S2) and C2[S2] < z:
                            S_sig.add(S)
                            coverage_change[S] = C2[S]
                            break
                    else:
                        continue
                    break
    return S_sig, coverage_change