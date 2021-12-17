import numpy as np
import pandas as pd
import json

np.random.seed(0)
large_val=100000

class box:
    def __init__(self, mins, maxs, freq, children=None):
        self.mins = mins 
        self.maxs = maxs
        if children is None:
            self.children = []
        else:
            self.children = children
        self.freq = freq 

    def volume_intersection(self, q):
        child_volume=0
        for i, c in enumerate(self.children):
            if q is None:
                child_volume += np.prod(np.array(c.maxs)-np.array(c.mins))
            else:
                child_volume += get_box_intersection_volume(q, c)
        if q is None:
            parent_volume = np.prod(np.array(self.maxs)-np.array(self.mins))
        else:
            parent_volume = get_box_intersection_volume(q, self)
        return parent_volume - child_volume

    def in_box(self, p):
        if p[0] > self.maxs[0] or p[0] < self.mins[0]:
            return False
        if p[1] > self.maxs[1] or p[1] < self.mins[1]:
            return False
        return True

    def in_bucket(self, p):
        if not self.in_box(p):
            return False

        for c in self.children:
            if c.in_box(p):
                return False

        return True

def a_fully_contains_b(a, b):
    if a.mins[0] <= b.mins[0] and a.mins[1] <= b.mins[1] and a.maxs[0] >= b.maxs[0] and a.maxs[1] >= b.maxs[1]:
        return True
    return False


def are_disjoint(a, b):
    if a.mins[0] >= b.maxs[0]:
        return True
    if a.mins[1] >= b.maxs[1]:
        return True
    if a.maxs[0] <= b.mins[0]:
        return True
    if a.maxs[1] <= b.mins[1]:
        return True
    return False

def boundary_overlaps(b, q):
    if a_fully_contains_b(b, q):
        return False
    if a_fully_contains_b(q, b):
        return False
    if are_disjoint(b, q):
        return False

    return True

def b_intersects_contains_q(b, q):
    for child in b.children:
        if a_fully_contains_b(child, q):
            return False

    if a_fully_contains_b(b, q):
        return True

    if not boundary_overlaps(b, q):
        return False

    return True


def find_intersections(q, curr_root, res):
    if are_disjoint(q, curr_root):
        return

    if b_intersects_contains_q(curr_root, q):
        res.append(curr_root)

    for child in curr_root.children:
        find_intersections(q, child, res)

def get_box_intersection_volume(q, b, should_print=False):
    if are_disjoint(q, b):
        return 0

    mins = [max([q.mins[0], b.mins[0]]), max([q.mins[1], b.mins[1]])]
    maxs = [min([q.maxs[0], b.maxs[0]]), min([q.maxs[1], b.maxs[1]])]
    if should_print:
        print( "mins", mins)
        print( "maxs", maxs)

    return np.prod(np.array(maxs)-np.array(mins))

def get_overlap_amount(q, b, dim):
    if q.mins[dim] >= b.maxs[dim]:
        return large_val
    if q.maxs[dim] <= b.mins[dim]:
        return large_val

    if q.mins[dim] >= b.mins[dim] and q.maxs[dim] <= b.maxs[dim]:
        return large_val

    if q.mins[dim] <= b.mins[dim] and q.maxs[dim] >= b.maxs[dim]:
        return b.maxs[dim]-q.mins[dim]

    if q.mins[dim] >= b.mins[dim]:
        return b.maxs[dim]-q.mins[dim]
    
    if q.maxs[dim] <= b.maxs[dim]:
        return b.maxs[dim]-q.mins[dim]

def get_q_res(q, D):
    count = 0
    for i in range(D.shape[0]):
        if not q.in_box(D[i]):
            continue
        count += 1

    return count

def count_int_points(q, b, noise_scale, D, remove=False):
    if are_disjoint(q, b):
        return 0, D
    count = 0
    keep_points = []
    for i in range(D.shape[0]):
        if not q.in_box(D[i]):
            keep_points.append(i)
            continue
        if not b.in_bucket(D[i]):
            keep_points.append(i)
            continue
        count += 1

    if remove:
        D = D[keep_points]
    else:
        i+=1

    return count + np.random.laplace(0, noise_scale), D

def get_intersecting_box(q, b):
    mins = [max([q.mins[0], b.mins[0]]), max([q.mins[1], b.mins[1]])]
    maxs = [min([q.maxs[0], b.maxs[0]]), min([q.maxs[1], b.maxs[1]])]

    return box(mins, maxs, 0)

def shrink_box(c, b, dim):
    if c.mins[dim] >= b.mins[dim]:
        c.mins[dim] = b.maxs[dim]
    else:
        c.maxs[dim] = b.mins[dim]
    

def shrink(b, q, t_bq, count_while_building):
    c = get_intersecting_box(q, b)
    
    participants = []
    for b_child in b.children:
        if boundary_overlaps(b_child, c):
            participants.append(b_child)

    while len(participants) != 0:
        min_size_change = large_val
        best_index = -1
        best_dim = -1
        for i, participant in enumerate(participants):
            for dim in [0, 1]:
                overlap = get_overlap_amount(c, participant, dim)
                if  overlap < min_size_change:
                    min_size_change = overlap
                    best_index = i
                    best_dim = dim

        shrink_box(c, participants[best_index], best_dim)

        participants = []
        for b_child in b.children:
            if boundary_overlaps(b_child, c):
                participants.append(b_child)

    for b_child in b.children:
        if a_fully_contains_b(b_child, c):
            return None, 0

    if count_while_building:
        count = count_int_points(c, b, D)
        if t_bq == 0 or b.volume_intersection(q) == 0:
            count = 0
        else:
            count = t_bq*b.volume_intersection(c)/b.volume_intersection(q)
    else:
        count = 0

    return c, count

def drill_hole(b, shrunk_box, t_bc, q):
    children_to_move = []
    for i, c in enumerate(b.children):
        if a_fully_contains_b(shrunk_box, c):
            children_to_move.append(i)
            shrunk_box.children.append(c)
    for i in reversed(children_to_move):
        b.children.pop(i)

    b.children.append(shrunk_box)
    b.freq = max([0, b.freq-t_bc])
    shrunk_box.freq = t_bc

def set_freq(curr_root, noise_scale, D):
    bucket_count=1
    q = box([-5, -5], [5, 5], 0)
    curr_root.freq, D = count_int_points(q, curr_root, noise_scale, D, True)
    #print(D.shape)

    for c in curr_root.children:
        c, D = set_freq(c, noise_scale, D)
        bucket_count += c

    return bucket_count, D


def get_answer(curr_root, q):
    if are_disjoint(q, curr_root):
        return 0

    ans = 0
    for c in curr_root.children:
        ans += get_answer(c, q)

    if curr_root.volume_intersection(None) != 0:
        ans += curr_root.freq*(curr_root.volume_intersection(q)/curr_root.volume_intersection(None))
    return ans

mins = [-5, -5]
maxs = [5, 5]

eps = 0.2
n = 1000
smooth=0.001

D = np.random.rand(n, 2)*10-5
q_size = 100
test_q_size = 100
#qs = [[min x min y], [max x, max y]]
qs = np.sort(np.random.rand(q_size, 2, 2)*10-5, axis=1)
test_qs = np.sort(np.random.rand(test_q_size, 2, 2)*10-5, axis=1)

qs = [box([qs[i, 0, 0], qs[i, 0, 1]], [qs[i, 1, 0], qs[i, 1, 1]], 0) for i in range(q_size)]
test_qs = [box([test_qs[i, 0, 0], test_qs[i, 0, 1]], [test_qs[i, 1, 0], test_qs[i, 1, 1]], 0) for i in range(test_q_size)]

test_ress = [get_q_res(q, D) for q in qs]

count_while_building=False


if count_while_building:
    q_intersects = []
    for i in range(len(qs)):
        count = 0
        for j in range(len(qs)):
            if are_disjoint(qs[i], qs[j]):
                continue
            count += 1 

        q_intersects.append(count)


root = box(mins, maxs, n)
for i, q in enumerate(qs):
    print("processing q", i)
    intersecting_boxes = []
    find_intersections(q, root, intersecting_boxes)

    for j, b in enumerate(intersecting_boxes):
        t_bq = 0
        if count_while_building:
            noise_scale = q_intersects[i]/eps
            t_bq = count_int_points(q, b, D, noise_scale)

        shrunk_box, t_bc = shrink(b, q, t_bq, count_while_building)
        if shrunk_box is None:
            continue

        drill_hole(b, shrunk_box, t_bc, q)

if not count_while_building:
    noise_scale = 1/eps
    set_freq(root, noise_scale, D)


err = 0
for i, q in enumerate(qs):
    res = get_answer(root, q)
    err += abs(res-test_ress[i])/np.maximum(test_ress[i],smooth*n)
print(err/q_size)
             


