"""Finite-hypothesis state-cost experiment, not a second output filter.

One variational selector would retain a cost for each admissible alternative,
not only the last emitted drawing. This diagnostic kernel tests that contract;
it is not integrated into the516 greedy mask search or production Unity.

Current shape evidence is integrated using dt/reference_seconds. The fixed
reference is the original516 sampling calibration, not the current render rate
or a fitted recovery timer. At one reference interval, original eta strength
is retained. Repartitioning physical time cannot manufacture more evidence.
"""
import math
import numpy as np

def edit_closure(raw,beta):
    raw=np.asarray(raw,float);assert raw.ndim==2 and raw.shape[0]==raw.shape[1]
    assert not np.isnan(raw).any()and(raw>=0).all();assert np.all(np.diag(raw)==0),'Nonzero identity edit is a correspondence failure'
    cost=raw*beta;paths=[[[]if i==j else[i,j]if math.isfinite(cost[i,j])else None for j in range(len(raw))]for i in range(len(raw))]
    for k in range(len(raw)):
        for i in range(len(raw)):
            for j in range(len(raw)):
                value=cost[i,k]+cost[k,j]
                if value<cost[i,j]:cost[i,j]=value;paths[i][j]=paths[i][k][:-1]+paths[k][j]if paths[i][k]and paths[k][j]else paths[i][k]or paths[k][j]
    return cost,paths

def close(values,cost):return np.min(np.asarray(values)[:,None]+cost,axis=0)

class StateCost:
    def __init__(self,raw,eta,initial=None,keys=None,reference_seconds=None):
        assert reference_seconds is not None and math.isfinite(reference_seconds)and reference_seconds>0
        self.reference_seconds=reference_seconds
        self.beta=float(np.float32(.14))*eta;self.cost,self.paths=edit_closure(raw,self.beta);n=len(self.cost);self.keys=list(range(n))if keys is None else keys;assert len(self.keys)==n
        value=np.zeros(n)if initial is None else np.asarray(initial,float);assert value.shape==(n,)and not np.isnan(value).any()
        self.value=close(value,self.cost);self.value-=self.value.min();self.seconds=0.
    def step(self,energy_rate,dt):
        if not math.isfinite(dt)or dt<0:raise ValueError('Invalid physical time interval')
        rate=np.asarray(energy_rate,float);assert rate.shape==self.value.shape and np.isfinite(rate).all();regret=rate-rate.min()
        # The closure is the reachable edit-history envelope within THIS state
        # cost, not another selected mask. Paths use unchanged raw edit edges.
        self.value=close(self.value+(dt/self.reference_seconds)*regret,self.cost);self.value-=self.value.min();self.seconds+=dt
        index=min(range(len(rate)),key=lambda i:(self.value[i],rate[i],self.keys[i]));return index

def restart_marginal(old_keys,old_values,new_keys,retained,required_feasible=None):
    """Drop only invalidated endpoint coordinates; preserve other evidence.

    required_feasible is the independently known current feasible support.
    A truncated bank must not pretend a missing combination is a reset pass.
    """
    if required_feasible is not None:
        missing=set(required_feasible)-set(new_keys)
        if missing:raise ValueError('MISSING_FEASIBLE_RESTART_COMBINATIONS:'+repr(sorted(missing)))
    marginal={}
    for key,value in zip(old_keys,old_values):
        projected=tuple(key[k]for k in retained);marginal[projected]=min(value,marginal.get(projected,math.inf))
    return np.array([marginal.get(tuple(key[k]for k in retained),math.inf)for key in new_keys])
