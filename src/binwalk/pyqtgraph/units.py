# -*- coding: utf-8 -*-
## Very simple unit support:
##  - creates variable names like 'mV' and 'kHz'
##  - the value assigned to the variable corresponds to the scale prefix
##    (mV = 0.001)
##  - the actual units are purely cosmetic for making code clearer:
##  
##    x = 20*pA    is identical to    x = 20*1e-12

## No unicode variable names (μ,Ω) allowed until python 3

SI_PREFIXES = 'yzafpnum kMGTPEZY'
UNITS = 'm,s,g,W,J,V,A,F,T,Hz,Ohm,S,N,C,px,b,B'.split(',')
allUnits = {}

def addUnit(p, n):
    g = globals()
    v = 1000**n
    for u in UNITS:
        g[p+u] = v
        allUnits[p+u] = v
    
for p in SI_PREFIXES:
    if p ==  ' ':
        p = ''
        n = 0
    elif p == 'u':
        n = -2
    else:
        n = SI_PREFIXES.index(p) - 8

    addUnit(p, n)

cm = 0.01






def evalUnits(unitStr):
    """
    Evaluate a unit string into ([numerators,...], [denominators,...])
    Examples:
        N m/s^2   =>  ([N, m], [s, s])
        A*s / V   =>  ([A, s], [V,])
    """
    pass
    
def formatUnits(units):
    """
    Format a unit specification ([numerators,...], [denominators,...])
    into a string (this is the inverse of evalUnits)
    """
    pass
    
def simplify(units):
    """
    Cancel units that appear in both numerator and denominator, then attempt to replace 
    groups of units with single units where possible (ie, J/s => W)
    """
    pass
    
    