def calculate_cop(T_l:float, T_h:float, ex_eta:float=1) -> float:
    """
    Calculates the cop of a carnot heat pump with an exergetic efficiency

    :param float T_l: Temperature of heat source in Celsius
    :param float T_h: Temperature of heat sink in Celsius
    :param float ex_eta: Exergetic efficiency 0<eta<1
    :return: cop of heat pump
    """
    return (1 - (T_l + 273) / (T_h+ 273)) ** -1 * ex_eta


def calculate_annuity_factor(r: float, t: float) -> float:
    """
    Calculates the annuity factor based on lifetime and interest rate

    Multiply the annualized costs with the annuity factor to get the up-front costs

    :param float r: interest rate (decimal)
    :param float t: lifetime in years
    :return: annuity factor
    """
    return (1-(1/(1+r)**t))/r

def calculate_profitable_relative_price(T_l:float, T_h:float, ex_eta:float=1) -> float:
    """
    Calculates the profitable relative price of a carnot heat pump

    :param float T_l: Temperature of heat source in Celsius
    :param float T_h: Temperature of heat sink in Celsius
    :param float ex_eta: Exergetic efficiency 0<eta<1
    :return: profitable relative price (same as cop)
    """
    return calculate_cop(T_l, T_h, ex_eta)

def calculate_allowable_investment_per_kw_el(T_l:float, T_h:float, h:int, p_th:float, p_el:float, r:float, t:float, ex_eta:float=1) -> float:
    """
    Calculates the allowable investment per kW for a carnot heat pump

    :param float T_l: Temperature of heat source in Celsius
    :param float T_h: Temperature of heat sink in Celsius
    :param int h: Operating hours per year
    :param float p_th: Cost of alternative heat generation in [currency]/MWh
    :param float p_el: Cost of electricity in [currency]/MWh
    :param float r: interest rate (decimal)
    :param float t: lifetime in years
    :param float ex_eta: Exergetic efficiency 0<eta<1
    :return: allowable investment costs in [currency]/kW
    """
    cop = calculate_cop(T_l, T_h, ex_eta)
    f = calculate_annuity_factor(r, t)
    return (p_th*cop/1000 - p_el/1000) * h * f
