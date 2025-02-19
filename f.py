P, x, y = map(int, input().split())

k = P / (2 * (x + y))

area = (k ** 2) * x * y

print(f"{area:.4f}")
