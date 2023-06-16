"""Calculates the multiplier and correction mass for an adduct"""

from typing import Optional, Tuple
import logging
import re
from molmass import Formula
from molmass import FormulaError
from matchms.constants import ELECTRTON_MASS

logger = logging.getLogger("matchms")


def get_multiplier_and_mass_from_adduct(adduct) -> Tuple[Optional[float], Optional[float]]:
    charge = get_charge_of_adduct(adduct)
    if charge is None:
        return None, None

    parent_mass, ions = get_ions_from_adduct(adduct)

    if parent_mass is None or ions is None:
        return None, None

    mass_of_ions = get_mass_of_ion(ions)
    if mass_of_ions is None:
        return None, None
    added_mass = mass_of_ions + ELECTRTON_MASS * -charge

    multiplier = 1/abs(charge)*parent_mass
    correction_mass = added_mass/(abs(charge))
    return multiplier, correction_mass


def get_ions_from_adduct(adduct):
    """Returns a list of ions from an adduct.

    e.g. '[M+H-H2O]2+' -> ["M", "+H", "-H2O"]
    """

    # Get adduct from brackets
    if "[" in adduct:
        ions_part = re.findall((r"\[(.*)\]"), adduct)
        if len(ions_part) != 1:
            logger.warning(f"Expected to find brackets [] once, not the case in {adduct}")
            return None, None
        adduct = ions_part[0]
    # Finds the pattern M or 2M in adduct it makes sure it is in between
    parent_mass = re.findall(r'(?:^|[+-])([0-9]?M)(?:$|[+-])', adduct)
    if len(parent_mass) != 1:
        logger.warning(f"The parent mass (e.g. 2M or M) was found {len(parent_mass)} times in {adduct}")
    parent_mass = parent_mass[0]
    if parent_mass == "M":
        parent_mass = 1
    else:
        parent_mass = int(parent_mass[0])

    ions_split = re.findall(r'([+-][0-9a-zA-Z]+)', adduct)
    ions_split = replace_abbreviations(ions_split)
    return parent_mass, ions_split


def split_ion(ion):
    sign = ion[0]
    ion = ion[1:]
    assert sign in ["+", "-"], "Expected ion to start with + or -"
    match = re.match(r'^([0-9]+)(.*)', ion)
    if match:
        number = match.group(1)
        ion = match.group(2)
    else:
        number = 1
    return sign, number, ion


def replace_abbreviations(ions_split):
    abbrev_to_formula = {'ACN': 'CH3CN', 'DMSO': 'C2H6OS', 'FA': 'CH2O2',
                         'HAc': 'CH3COOH', 'Hac': 'CH3COOH', 'TFA': 'C2HF3O2',
                         'IsoProp': 'CH3CHOHCH3', 'MeOH': 'CH3OH'}
    corrected_ions = []
    for ion in ions_split:
        sign, number, ion = split_ion(ion)
        if ion in abbrev_to_formula:
            ion = abbrev_to_formula[ion]
        corrected_ions.append(sign + str(number) + ion)
    return corrected_ions


def get_mass_of_ion(ions):
    added_mass = 0
    for ion in ions:
        sign, number, ion = split_ion(ion)
        try:
            formula = Formula(ion)
            atom_mass = formula.isotope.mass
        except FormulaError:
            logger.warning(f"The formula {ion} in the adduct is not recognized")
            return None
        if sign == "-":
            number = -int(number)
        else:
            number = int(number)
        added_mass += number * atom_mass
    return added_mass


def get_charge_of_adduct(adduct)->Optional[int]:
    charge = re.findall((r"\]([0-9]?[+-])"), adduct)
    if len(charge) != 1:
        logger.warning(f'Charge was found {len(charge)} times in adduct {adduct}')
        return None
    charge = charge[0]
    if len(charge) == 1:
        charge_size = "1"
        charge_sign = charge
    elif len(charge) == 2:
        charge_size = charge[0]
        charge_sign = charge[1]
    else:
        logger.warning(f"Charge is expected of length 1 or 2 {charge} was given")
        return None
    return int(charge_sign+charge_size)
