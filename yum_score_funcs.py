def normalise_points(min, max, score):
    """
    Normalize a score to a 0–1 range.

    Parameters:
        min (float): The minimum possible value.
        max (float): The maximum possible value.
        score (float): The actual score to normalize.

    Returns:
        float: The normalized score between 0 and 1.
    """
    normal_points = (score - min) / (max - min)
    return normal_points


def yum_score(a_points, f_points, b_points, u_points):
    """
    Calculate the average 'yum' score from four component scores.

    Parameters:
        a_points (float): Score for attribute Aroma.
        f_points (float): Score for attribute Flavour.
        b_points (float): Score for attribute Body.
        u_points (float): Score for attribute Uniformity.

    Returns:
        float: The average yum score between 0 and 1.
    """
    total_points = a_points + f_points + b_points + u_points
    y_score = total_points / 4
    return y_score