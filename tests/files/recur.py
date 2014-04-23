def f(i):
	if i < 1:
		return 0
	else:
		return i + f(i-1)

a = f(2)
b = f(5)
c = f(f(2))