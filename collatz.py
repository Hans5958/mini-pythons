import math

n = int(input("Number: "))

print(n)
while not n == 1:
	if n%2: # odd
		n = n * 3 + 1
	else: # even
		n = math.floor(n / 2)
	print(str(n), end=", ")