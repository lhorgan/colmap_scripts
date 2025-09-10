import numpy as np
from scipy.stats import ortho_group
from procrustes import orthogonal

# random input 10x7 matrix A
a = np.random.rand(10, 7)

# random orthogonal 7x7 matrix T (acting as Q)
t = ortho_group.rvs(7)

# target matrix B (which is a shifted AT)
b = np.dot(a, t) + np.random.rand(1, 7)

# orthogonal Procrustes analysis with translation
result = orthogonal(a, b, scale=True, translate=True)

# compute transformed matrix A (i.e., A x Q)
aq = np.dot(result.new_a, result.t)

# display Procrustes results
print("Procrustes Error = ", result.error)
print("\nDoes the obtained transformation match variable t? ", np.allclose(t, result.t))
print("Does AQ and B matrices match?", np.allclose(aq, result.new_b))

print("Transformation Matrix T = ")
print(result.t)
print("")
print("Matrix A (after translation and scaling) = ")
print(result.new_a)
print("")
print("Matrix AQ = ")
print(aq)
print("")
print("Matrix B (after translation and scaling) = ")
print(result.new_b)