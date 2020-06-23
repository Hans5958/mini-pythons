n = int(input("How much? "))

assert n > 0 

sequence = [0, 1]
i = 1

while i < n:
	i += 1
	next = sequence[-1]+sequence[-2]
	print(str(i) + ". " + str(next))
	sequence.append(next)

