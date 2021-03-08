import numpy as np
from scipy.stats import rankdata
from scipy.stats import pearsonr
# from sklearn.metrics import mutual_info_score

# def calc_MI(x, y, bins):
#     c_xy = np.histogram2d(x,y,bins)[0]
#     mi = mutual_info_score(None, None, contingency=c_xy)
#     return mi

# def range_calc_MI(matrix, i: int):
#     mi = np.zeros(shape=(matrix.shape[0]))

#     for j in range(i+1, matrix.shape[0]):
#         mi[j] = calc_MI(matrix.iloc[i,:], matrix.iloc[j,:], 2)

#     return mi

def range_calc_Cor(matrix, ii: list):
    cor = np.zeros(shape=(len(ii), matrix.shape[0]), dtype=object)

    for i in ii:
        for j in range(i+1, matrix.shape[0]):
            temp_cor = pearsonr(matrix.iloc[i,:], matrix.iloc[j,:])
            if temp_cor[1]<0.05:
                i_idx = i-ii[0]
                cor[i_idx, j] = temp_cor[0], temp_cor[1]

    return cor

def fdr(p_vals):
    ranked_p_values = rankdata(p_vals)
    fdr = p_vals * len(p_vals) / ranked_p_values
    fdr[fdr > 1] = 1

    return fdr