import numpy as np

def kabsch_umeyama(A, B):
    assert A.shape == B.shape
    n, m = A.shape

    EA = np.mean(A, axis=0)
    EB = np.mean(B, axis=0)
    VarA = np.mean(np.linalg.norm(A - EA, axis=1) ** 2)

    H = ((A - EA).T @ (B - EB)) / n
    U, D, VT = np.linalg.svd(H)
    d = np.sign(np.linalg.det(U) * np.linalg.det(VT))
    S = np.diag([1] * (m - 1) + [d])

    R = U @ S @ VT
    c = VarA / np.trace(np.diag(D) @ S)
    t = EA - c * R @ EB

    return R, c, t

A = np.array([[ 23, 178, 30],
              [ 66, 173, 10],
              [ 88, 187, 12],
              [119, 202, 15],
              [122, 229, 40],
              [170, 232, 15],
              [179, 199, 40]])
B = np.array([[232, 38,10],
              [208, 32, 3.33],
              [181, 31, 4],
              [155, 45, 5],
              [142, 33, 13.33],
              [121, 59, 5],
              [139, 69, 13.33]])

R, c, t = kabsch_umeyama(A, B)
# R = [[-0.81034281,  0.58595608]
#      [-0.58595608, -0.81034281]]
# c = 1.46166131
# t = [271.3345951, 396.07800317]

B = np.array([t + c * R @ b for b in B])
# B = [[ 29.08878779, 152.36814188]
#      [ 52.37669337, 180.03008629]
#      [ 83.50028582, 204.33920503]
#      [126.28647155, 210.02515345]
#      [131.40664707, 235.37261559]
#      [178.54823113, 222.56285654]
#      [165.79288328, 195.30194121]]

print(B[0])