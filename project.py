import numpy as np
from constraint import *

#function to print the timetable
def print_timetable(s):
	print("%-5s %-10s %-10s %-10s %-10s %-10s %-10s %-10s %-10s %-10s" % ("CODE", "NAME", "SURNAME", "MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"))
	for i in range(len(workers)): 
		print("%-5s %-10s %-10s %-10s %-10s %-10s %-10s %-10s %-10s %-10s" % (workers[i]['code'],
																		workers[i]['name'], 
																		workers[i]['surname'],
																		s[nametable[i,0]], 
																		s[nametable[i,1]], 
																		s[nametable[i,2]], 
																		s[nametable[i,3]], 
																		s[nametable[i,4]], 
																		s[nametable[i,5]], 
																		s[nametable[i,6]]))

#function to read the input files
def read_lines(filename):
	file = open(filename, "r")
	temp = file.read().split("\n")
	file.close()
	return temp

#function to compute the constraints
def cardinality(*l, key):
	sum = 0
	if key == 'all':
		for var in l:
			if var != 'home':
				sum = sum + 1
	elif key == 'milk':
		for var in l:
			if var == 'milk':
				sum = sum + 1
	elif key == 'accountant':
		for var in l:
			if var == 'accountant':
				sum = sum + 1
	elif key == 'transport':
		for var in l:
			if var == 'transport':
				sum = sum + 1
	elif key == 'cleaning':
		for var in l:
			if var == 'cleaning':
				sum = sum + 1
	elif key == 'home':
		for var in l:
			if var == 'home':
				sum = sum + 1	
	return sum

#function to create the list to be used to satisfy a specific contraint
def create_specific_list(key):
	new_list  = np.empty((len(workers), days), dtype="<U100")
	trash = []
	for j in range(days):
		for worker in workers:
			if worker[key] == 'Y':
				new_list[workers.index(worker),j] = nametable[workers.index(worker),j]
			else:
				trash.append(workers.index(worker))

	# delete from the new list the empty elements 
	new_list = np.delete(new_list, trash, 0)
	while len(trash) > 0 : trash.pop()
	return new_list

# read workers profiles
lines = read_lines("worker_profiles")
# list of dictionaries, each dict represents a worker
workers = [] 
tags = lines[0].split()
for line in lines[1:]:
	worker = {}
	tokens = line.split()
	for i in range(len(tags)):
		worker[tags[i]] = tokens[i]
	workers.append(worker)

# read requirements table
rows = read_lines("requirements_table")
k = eval(rows[0].split()[1])
# dict of lists, each list represents a specific requirement
required = {} 
for row in rows[1:]:
	labels = row.split()
	required[labels[0]] = []
	for tok in labels[1:]:
		required[labels[0]].append(tok)

days = len(required['total'])
week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

# matrix that represents the names of the variables
# each row represents a worker
# each column represents half of a day
nametable = np.empty((len(workers), days), dtype="<U100")

# create problem
problem = Problem()

# insertions of variables guaranteeing node-consistency
for i in range(len(workers)):
	for j in range(days):
		nametable[i,j] = str(i)+","+str(j)
		domain = ['home']
		if workers[i]['holidays'] == 'N':
			domain.append('standard')
			if workers[i]['milk'] == 'Y':
				domain.append('milk')
			if workers[i]['transport'] == 'Y':
				domain.append('transport')
			if workers[i]['accountant'] == 'Y':
				domain.append('accountant')
			if workers[i]['cleaning'] == 'Y':
				domain.append('cleaning')
		problem.addVariable(nametable[i][j], domain)

#constraints

# minimum number of workers
for j in range(days):
	problem.addConstraint (lambda *v, j = j: cardinality(*v, key = 'all') == eval(required['total'][j]), nametable[:,j].tolist())

# max 5 working days per worker
for i in range(len(workers)):
	problem.addConstraint (lambda *v, i = i: cardinality(*v, key='all') <= 5 , nametable[i,:].tolist())

# create the list of variables representing workers with attribute milk
yes_milk = create_specific_list('milk')
#guaranteed at least one worker with attribute MILK
for j in range(days):
	problem.addConstraint (lambda *v, j = j: cardinality(*v, key='milk') == eval(required['milk'][j]), yes_milk[:,j].tolist())

# create the list of variables representing workers with attribute truck
truck = create_specific_list('transport')
#guaranteed at least one truck for each turn
for j in range(days):
	problem.addConstraint (lambda *v, j = j: cardinality(*v, key='transport') == eval(required['transport'][j]), truck[:,j].tolist())

# create the list of variables representing workers with attribute accountant
accountant = create_specific_list('accountant')
#guaranteed at least one accountant for each turn
for j in range(days):
	problem.addConstraint (lambda *v, j = j: cardinality(*v, key='accountant') == eval(required['accountant'][j]), accountant[:,j].tolist())

# create the list of variables representing workers with attribute cleaning
cleaning = create_specific_list('cleaning')
# mimimum number of cleaning workers
for j in range(days):
	problem.addConstraint (lambda *v, j = j: cardinality(*v, key='cleaning') == eval(required['cleaning'][j]), cleaning[:,j].tolist())

# manage permission days
free_days = []
for w in week:
	for worker in workers:
		if worker['free-day'] == w or worker['permission'] == w:
			free_days.append(nametable[workers.index(worker), week.index(w)])
		
problem.addConstraint (lambda *v : cardinality(*v, key='all') == 0, free_days)

# worker in holiday
#since we have guaranteed node-consistency, the domain of these workers is [home], hence no constraint has to be add

# compute solutions
solutions = problem.getSolutions()

#print a generic solution 
print("CSP solution:")
print_timetable(solutions[0])
print("")

# compute the cost of each solution
costs = []
for sol in solutions:
	cost = 0
	for var in sol:
		if sol[var] != 'home':
			#each day has a total of 8 work hour
			cost = cost + eval(workers[eval(var[0])]['hourly-rate'])*8
	costs.append(cost)

#take the cheapest solution
least_cost_solution = solutions[costs.index(min(costs))]
#print the solution
print("Weighted CSP solution:")
print_timetable(least_cost_solution)
print("Cost: "+str(min(costs))+"\n")


# compute the preference of each solution
pref_dict = {'standard': 'standard-pref', 'milk': 'milk-pref', 'transport': 'transport-pref', 'accountant': 'accountant-pref', 'cleaning': 'cleaning-pref'}
prefs = []
for sol in solutions:
	min_pref = 1
	for var in sol:
		if sol[var] != 'home':
			current_pref = eval(workers[eval(var[0])][pref_dict[sol[var]]])
			if current_pref < min_pref:
				min_pref = current_pref
	prefs.append(min_pref)

#take the most preferred one
max_pref_solution = solutions[prefs.index(max(prefs))]
#print the solutions
print("Fuzzy CSP solution: ")
print_timetable(max_pref_solution)
print("Preference: "+str(max(prefs))+"\n") 
'''
#merge the cheapest and the most preferred solution
tolerance = 1.05 * min(costs)
merge_solutions = []
newCost = []
for i in range (len(solutions)):
	if costs[i] < tolerance:
		merge_solutions.append(solutions[i])
		newCost.append(costs[i])

merge_pref = []
for sol in merge_solutions:
	min_pref = 1
	for var in sol:
		if sol[var] != 'home':
			current_pref = eval(workers[eval(var[0])][pref_dict[sol[var]]])
			if current_pref < min_pref:
				min_pref = current_pref
	merge_pref.append(min_pref)

merge_solution = merge_solutions[merge_pref.index(max(merge_pref))]

print("Merged solution: ")
print_timetable(merge_solution)
print("Preference: "+str(max(merge_pref)))
print("Cost: "+str(min(newCost))) 
print(len(solutions)-len(merge_solutions))
'''

# compute the max cost of the solutions
costs = []
for sol in solutions:
	cost = 0
	for var in sol:
		if sol[var] != 'home':
			cost = cost + eval(workers[eval(var[0])]['hourly-rate'])*8
	costs.append(cost)
max_cost = max(costs)

# compute the score of each solution
pref_dict = {'standard': 'standard-pref', 'milk': 'milk-pref', 'transport': 'transport-pref', 'accountant': 'accountant-pref', 'cleaning': 'cleaning-pref'}
scores = []
costs = []
prefs = []
for sol in solutions:
	cost = 0
	min_pref = 1
	for var in sol:
		if sol[var] != 'home':
			cost = cost + eval(workers[eval(var[0])]['hourly-rate'])*8
			current_pref = eval(workers[eval(var[0])][pref_dict[sol[var]]])
			if current_pref < min_pref:
				min_pref = current_pref
	costs.append(cost)
	prefs.append(min_pref)
	score = k*min_pref + (1-k)*(1-cost/max_cost)
	scores.append(score)

#take the highest scored one
max_score_solution = solutions[scores.index(max(scores))]
#print the solutions
print("Trade-off solution with k = "+str(k)+":")
print_timetable(max_score_solution)
print("Preference: "+str(prefs[scores.index(max(scores))]))
print("Cost: "+str(costs[scores.index(max(scores))]))
print("Total score: "+str(max(scores))+"\n")