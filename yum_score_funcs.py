### normalise_points() returns a score from 0-1
def normalise_points(min, max, score):
    normal_points = (score - min) / (max - min)
    return normal_points


### yum_score() returns a score from 0-1
def yum_score(a_points, f_points, b_points, u_points):
    total_points = a_points + f_points + b_points + u_points
    y_score = total_points / 4
    return y_score