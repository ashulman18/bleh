import itertools
import numpy as np
from collections import defaultdict


class QualPOMDP:
	# 1
	def __init__(self, attmps, sesh, trans, ff, fp, pff, pfp, pq, dis):
		self.exam_attempts = attmps
		self.exams_per_session = sesh
		self.transition = trans
		self.r_false_fail = ff
		self.r_false_pass = fp
		self.p_false_fail = pff
		self.p_false_pass = pfp
		self.p_qualified = pq
		self.discount = dis

	# 2
	def space(self,x,n): 
		self.space = [i for i in itertools.product(x, repeat = n)]
	def action(self,x,n): 
		self.action = [i for i in itertools.product(x, repeat = n)]
	def observation(self,x,n): 
		self.observation = [i for i in itertools.product(x, repeat = n)]

	# 3
	def transitionFN(self, p, s, a, sp):
		# just p / num exams to take except for edges
		# we need to know how many exams they are studying for p
		suma = 0
		for i, exam in enumerate(a):
			suma += a[i]
			if a[i] == 0 and s[i] != sp[i]:
				return 0
			# if they take the test but are qualified they don't need to transition
			elif a[i] == 1 and s[i] == 1:
				suma -= 1
		if suma == 0 and s == sp: return 1
		elif suma == 0 and s != sp: return 0
		elif s == sp and s == [1,1,1]: return 1

		return self.transition / suma

	# 4 
	def rewardFN(self, p, s, a, t):
		# false pass at any time step
		if s != [1,1,1] and a == [0,0,0]: return -1
		# false fails at time 3
		# faculty do not pass a fully qualified candidate
		elif t == 3 and a != [0,0,0] and s == [1,1,1]: return -1
		return 0

	# 5
	def observationFN(self, p, a, sp, o):
		# probability partials
		probs = [0,0,0]
		# total = 1
		for i, exam in enumerate(a):
			# don't take exam, observe no exam
			if (a[i] == 0 and o[i] == -1):
				probs[i] = 1
			# take exam but the observation is no exam or don't take the exam, observation is p/f
			elif (a[i] == 1 and o[i] == -1) or (a[i] == 0 and o[i] != -1):
				probs[i] = 0
			# pass exam, are qualified
			elif (o[i] == 1 and sp[i] == 1):
				probs[i] = 1 - self.p_false_fail
			# fail exam, are qualified
			elif (o[i] == 0 and sp[i] == 1):
				probs[i] = self.p_false_fail
			# pass exam, are not qualified
			elif (o[i] == 1 and sp[i] == 0):
				probs[i] = self.p_false_pass
			# fail exam, are not qualified
			elif (o[i] == 0 and sp[i] == 0):
				probs[i] = 1 - self.p_false_pass
		return np.prod(probs)

	# 6
	# it's the probability of being in each state!
	def initbelief(self, p):
		beliefs = []
		for i, state in enumerate(self.space):
			# for each exam they are already qualified in, *.9
			# prob they are qualified in those
			quald = self.p_qualified ** state.count(1)
			# prob they aren't qualified in others
			nquald = (1 - self.p_qualified) ** state.count(0)
			beliefs.append(round(quald*nquald,3))
		return beliefs
		# result: [2, 3, 0.3, -1.0, -1.0, 0.15, 0.2, 0.9]
    
	# 7
	def belief_update(self, p, b, a, o):
		#  O(o|sp,a) * sum ( T(sp|s,a)b(s) )
		upbeliefs = []
		tr = 0
		# go through each state to update the belief after action
		for i, state in enumerate(self.space):
			# O(o|sp, a) 
			ob = self.observationFN(p, a, state, o)
			# print(ob)
			# print(state)
			for j, prestate in enumerate(self.space):
				# sum ( T(sp|s,a)b(s) )
				# print(prestate)
				# print(self.transitionFN(p, prestate, a, state))
				# print(b[j])
				tr += self.transitionFN(p, prestate, a, state)*b[j]
				# print(tr)
			# print(ob)
			# print(round(ob*tr,4))
			upbeliefs.append(round(ob*tr,4))
			tr,ob = 0,0
		return upbeliefs

	# 9: are they saying they're failing a qualified person?
	def last_reward(self, p, s, o):
		# student fails at least one exam, but is qualified
		if s == [1,1,1] and (0 in o):
			return -1
		# student is not proficient in all, but passes all tests
		elif (0 in s) and o == [1,1,1]:
			return -1
		return 0
	
	# 10
	def exp_utility(self, p, s, o):
		# fail any
		if 0 in o:
			# must retake all
			sumit = 0
			for i, sp in enumerate(self.space):
				# probability of observation (exam results) x reward of action after results
				sumit += self.observationFN(p, [1,1,1], sp, o)*self.rewardFN(p, sp, [1,1,1], 3)
			return sumit
		# pass all
		# should be 0 if qualified, -1 if not
		return self.rewardFN(p, s, [0,0,0], 2)

	# 11
	# should have as many elements as there are states
	# utility of a belief state is the maximum value of  alphixb(s)
	# vectors represent immediate reward after an action
	def alph_vectors(self, p):
		stateSum = 0
		obsSum = 0
		alphvec = []
		for state in self.space:
			# for s2 in self.space:
			# 	if t == 1:
			# 		stateSum += self.transitionFN(p, state, [1,1,1], s2)
			# 	elif t == 2:
			# 		take exams they failed
			# 	elif t == 3:
			# 		if passed all:
			# 			stateSum += self.transitionFN(p, state, [0,0,0], s2)
			# 		else:
			# 			stateSum += self.transitionFN(p, state, [1,1,1], s2)
			# for obs in self.observation:
			# 	obsSum += self.observationFN(p, a, state, obs)
			# eu = exp_utility(p,state,o)
			alphvec.push(stateSum + obsSum + eu)
		print alphvec
		return alphvec

	# 12
	# should have as many elements as there are states
	# utility of a belief state is the maximum value of  alphixb(s)
	# vectors represent immediate reward after an action
	def alph_vectors_retake(self, p):
		stateSum = 0
		obsSum = 0
		alphvec = []
		for state in self.space:
			# for s2 in self.space:
			# 	if t == 1:
			# 		stateSum += self.transitionFN(p, state, [1,1,1], s2)
			# 	elif t == 2:
			# 		take exams they failed
			# 	elif t == 3:
			# 		if passed all:
			# 			stateSum += self.transitionFN(p, state, [0,0,0], s2)
			# 		else:
			# 			action = retake failed
			# 			stateSum += self.transitionFN(p, state, failed, s2)
			# for obs in self.observation:
			# 	obsSum += self.observationFN(p, a, state, obs)
			# eu = exp_utility(p,state,o)
			alphvec.push(stateSum + obsSum + eu)
		print alphvec
		return alphvec


# 1
QPOMDP = QualPOMDP(2, 3, 0.3, -1., -1., 0.15, 0.2, 0.9, 1);

# 2
QPOMDP.space([0,1],3)
print(QPOMDP.space)
# Result: [(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)]
QPOMDP.action([0,1],3)
print(QPOMDP.action)
# Result: [(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)]
QPOMDP.observation([-1,0,1],3)
print(QPOMDP.observation)
# Result: [(-1, -1, -1), (-1, -1, 0), (-1, -1, 1), (-1, 0, -1), (-1, 0, 0), (-1, 0, 1), (-1, 1, -1), (-1, 1, 0), 
# (-1, 1, 1), (0, -1, -1), (0, -1, 0), (0, -1, 1), (0, 0, -1), (0, 0, 0), (0, 0, 1), (0, 1, -1), (0, 1, 0), (0, 1, 1), 
# (1, -1, -1), (1, -1, 0), (1, -1, 1), (1, 0, -1), (1, 0, 0), (1, 0, 1), (1, 1, -1), (1, 1, 0), (1, 1, 1)]

# 3
print(QPOMDP.transitionFN(QualPOMDP, [0,1,0], [1,1,0], [1,1,0]))
# Result: 0.15

# 4
print(QPOMDP.rewardFN(QualPOMDP, [1,0,0], [0,0,0], 3))
# Result: -1

# 5
print(sum(QPOMDP.observationFN(QualPOMDP, [1,1,1], [1,1,1], o) for o in QPOMDP.observation))
# Result: 1.0

# 6
print(QPOMDP.initbelief(QualPOMDP))
# Result: [0.001, 0.009, 0.009, 0.081, 0.009, 0.081, 0.081, 0.729]

# 7
print(QPOMDP.belief_update(QualPOMDP, QPOMDP.initbelief(QualPOMDP), [1,1,1], [1,1,1])) # = .933
# Result: [0.0008, 0.0034, 0.0034, 0.0145, 0.0034, 0.0145, 0.0144, 0.0614]
print(QPOMDP.belief_update(QualPOMDP, QPOMDP.initbelief(QualPOMDP), [1,1,1], [1,1,0]))
# Result: [0.0032, 0.0006, 0.0136, 0.0026, 0.0136, 0.0026, 0.0578, 0.0108]

# belief reward sum
# 8
bel_rew_sum = 0
act_rew = defaultdict(int)
for act in QPOMDP.action:
	for i, sprob in enumerate(QPOMDP.initbelief(QualPOMDP)):
		bel_rew_sum += sprob*QPOMDP.rewardFN(QualPOMDP, QPOMDP.space[i], act, 1)
		# for each action, the probability we are in the state * the reward for it
	act_rew[act] = bel_rew_sum
print(act_rew)
# Result: defaultdict(<type 'int'>, {(0, 1, 1): 0.0, (1, 1, 0): 0.0, (1, 0, 0): 0.0, 
	# (0, 0, 1): 0.0, (1, 0, 1): 0.0, (0, 0, 0): 0.0, (0, 1, 0): 0.0, (1, 1, 1): 0.0})
	# Where the key is the set of actions and the value is the expected immediate reward

# 9
print(QPOMDP.last_reward(QualPOMDP, [1,1,1], [1,1,-1]))
# Result: 0

# 10
print(QPOMDP.exp_utility(QualPOMDP, [1,1,1], [1,1,0]))
# Result: 0.0

