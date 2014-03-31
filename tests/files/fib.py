#Allocate list for output 0-9
o = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0]

i = 2

while i < 10:
	o[i] = o[i-1] + o[i-2]
	i = i + 1

#TODO: Add More implemnations of fib (i.e. o = list(10), i+=1 and function for fib)
