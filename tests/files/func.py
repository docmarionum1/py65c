def f(x, y=1):
	return x + y

a = f(1, 2)
b = 2 + f(1, 2)
c = f(1, 2) + f(1, 2)

d = f(1)
e = f(4)
g = f(1, y=3)

def h(x, y, z):
    return x*y-z

i = h(5, 3, 6)
j = h(8, 4, 12)

def k(r, s=4, t=f(5,5)):
    return t-s-r

l = k(1, s=2)
m = k(2, t=20)
