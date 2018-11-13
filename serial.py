import math
import operator as op
import os
import pickle
import random
from collections import defaultdict

from scipy.special import comb
from generate_random_graph import generate_filepath_pickle
from timer import time_find_k_seeds, runtimes, runtimes_to_csv, time_cumulatively, cumulative_runtimes_to_csv

L_CONSTANT = 1
EPSILON_CONSTANT = 0.2
K_CONSTANT = 2

TWITTER_DATASET_FILEPATH = './datasets/twitter'
TWITTER_DATASET_PICKLE_FILEPATH = './datasets/twitter.pickle'
EDGE_FILE_SUFFIX = '.edges'
RANDOM_CSR_GRAPH_FILEPATH = './datasets/random_graph.pickle'

def node_selection_experimental(graph, k, theta):
    # Initialize empty set R
    R = {}
    # Generate theta random RR sets and insert them into R
    for i in range(theta):
        R[i] = random_reverse_reachable_set(graph)
    # Initialize a empty node set S_k
    S_k = []
    
    R_used = {}
    for j in range(k):
        # Identify node v_j that covers the most RR sets in R
        v_j, sets_to_remove = find_most_common_node(R)
        # Add v_j into S_k
        S_k.append(v_j)
        # Remove from R all RR sets that are covered by v_j
        for set_id in sets_to_remove:
            R_used = R[set_id]
            del R[set_id]
    return S_k, R, R_used
    
def phase_3_experimental(R,R_used,S_k,k,max_iter):
    go = True
    count = 0
    
    while go:
        # Calculate marginal contributions and which sets make them up
        marginal_contribution = defaultdict(int)
        marginal_count = defaultdict(int)
        seeds_per_RR = defaultdict(int)
        for set_id, rr_set in R_used.items():
            num_seeds = 0
            unique_seed = -1
            for node in rr_set:
                if node in S_k:
                    num_seeds += 1
                    unique_seed = node
                    if num_seeds > 1:
                        break
            if num_seeds == 1:
                marginal_contribution[unique_seed].append[set_id]
                if unique_seed in marginal_count:
                    marginal_count[unique_seed] += 1
                else:
                    marginal_count[unique_seed] = 0
        # Marginal number of RR sets each seed provides is tabulated
        # Now select one seed to return and add its sets in marginal_contribution
        # back into R before finding a new k^th seed
        
        leaving_seed = min(marginal_count, key = marginal_count.get)
        S_k.remove(leaving_seed)
        for set_id in marginal_contribution[leaving_seed]:
            R[set_id] = R_used[set_id]
            del R_used[set_id]
        
        # Select new k^th seed
        
        node, sets_to_remove = find_most_common_node(R)
        S_k.append(node)
        for set_id in sets_to_remove:
            R_used[set_id] = R[set_id]
            del R[set_id]
        
        count += 1
        
        if node == leaving_seed or count >= max_iter:
            go = False
    return S_k

def width(graph, nodes):
    """ Returns the number of edges in a graph """
    count = 0
    for node in nodes:
        value_start = graph[1][node]
        value_end = graph[1][node + 1]
        count += value_end - value_start
    return count

def find_most_common_node(rr_sets):
    counts = defaultdict(int)
    exists_in_set = defaultdict(list)
    maximum = 0
    most_common_node = 0
    for set_id, rr_set in rr_sets.items():
        for node in rr_set:
            exists_in_set[node].append(set_id)
            counts[node] += 1
            if counts[node] > maximum:
                most_common_node = node
                maximum = counts[node]
    return most_common_node, exists_in_set[most_common_node]
        
def node_selection(graph, k, theta):
    # Initialize empty set R
    R = {}
    # Generate theta random RR sets and insert them into R
    for i in range(int(math.ceil(theta))):
        R[i] = random_reverse_reachable_set(graph)
    # Initialize a empty node set S_k
    S_k = []
    for j in range(k):
        # Identify node v_j that covers the most RR sets in R
        v_j, sets_to_remove = find_most_common_node(R)
        # Add v_j into S_k
        S_k.append(v_j)
        # Remove from R all RR sets that are covered by v_j
        for set_id in sets_to_remove:
            del R[set_id]
    return S_k

def calculate_lambda(n, k, l, e):
    return (8.0 + 2 * e) * n * (l * math.log(n) + math.log(comb(n, k)) + math.log(2)) * e ** -2
    
def random_reverse_reachable_set(graph):
    """ Returns a set of reverse reachable nodes from a random seed node """
    n = len(graph[1]) - 1
    start = random.choice(range(n))
    stack = [start]
    visited = set()
    while stack:
        curr = stack.pop()
        if curr not in visited:
            visited.add(curr)

            # We are getting the value offsets from the second array here
            value_start = graph[1][curr]
            value_end = graph[1][curr + 1]

            # Using the offsets we just extracted, get head of outgoing edges
            edges = graph[2][value_start:value_end]

            # Do the same with the values of the edges
            probabilities = graph[0][value_start:value_end]

            # assert for correctness
            assert(len(edges) == len(probabilities))

            for i in range(len(edges)):
                if random.random() < probabilities[i]:
                    stack.append(edges[i])
    return visited
    
def kpt_estimation(graph, k):
    n = len(graph[1]) - 1
    m = len(graph[0])
    for i in range(1, int(math.log(n, 2))):
        ci = 6 * L_CONSTANT * math.log(n)  + 6 * math.log(math.log(n, 2)) * 2**i
        cum_sum = 0
        for j in range(int(ci)):
            R = random_reverse_reachable_set(graph)
            w_r = width(graph, R)
            k_r = 1 - (1 - (w_r / m))**k
            cum_sum += k_r
        if (cum_sum / ci) > 1/(2**i):
            return n * cum_sum / (2 * ci)
    return 1.0

@time_find_k_seeds
def find_k_seeds(graph, k):
    kpt = kpt_estimation(graph, k)
    lambda_var = calculate_lambda(len(graph[1]) - 1, k, L_CONSTANT, EPSILON_CONSTANT)
    theta = lambda_var / kpt
    return node_selection(graph, k ,theta)

if __name__ == "__main__":
    for i in range(20, 41):
        for j in range(50):
            graph = pickle.load(open(generate_filepath_pickle(i), "rb"))
            print(find_k_seeds(graph, K_CONSTANT))
    with open("runtimes.csv", "w") as fp:
        fp.write(runtimes_to_csv())
    
