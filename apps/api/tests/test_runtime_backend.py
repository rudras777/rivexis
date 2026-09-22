from __future__ import annotations

from rivexis_api.runtime_backend import RedisControlPlane


class FakeRedis:
    def __init__(self):
        self.zsets={};self.hashes={};self.expiries={}
    def eval(self,script,nkeys,key,cutoff,now,member,limit):
        z=self.zsets.setdefault(key,{})
        for k,v in list(z.items()):
            if float(v)<=float(cutoff):z.pop(k,None)
        if len(z)>=int(limit):return 0
        z[str(member)]=float(now);return 1
    def hgetall(self,key):return dict(self.hashes.get(key,{}))
    def hincrby(self,key,field,amount):
        h=self.hashes.setdefault(key,{})
        h[field]=int(h.get(field,0))+int(amount);return h[field]
    def hset(self,key,mapping):self.hashes.setdefault(key,{}).update(mapping)
    def expire(self,key,seconds):self.expiries[key]=seconds
    def delete(self,key):self.hashes.pop(key,None);self.zsets.pop(key,None)


def test_redis_control_plane_is_workspace_scoped_and_opens_circuit():
    redis=FakeRedis(); backend=RedisControlPlane(redis)
    assert backend.consume_budget("w1","rpc",100.0,1)
    assert not backend.consume_budget("w1","rpc",101.0,1)
    assert backend.consume_budget("w2","rpc",101.0,1)
    first=backend.failure("w1","rpc",102.0,2,30.0)
    assert first.consecutive_failures==1 and first.opened_until==0
    second=backend.failure("w1","rpc",103.0,2,30.0)
    assert second.consecutive_failures==2 and second.opened_until==133.0
    assert backend.circuit("w1","rpc",104.0).opened_until==133.0
    backend.success("w1","rpc")
    assert backend.circuit("w1","rpc",105.0).consecutive_failures==0


def test_redis_budget_members_are_unique_across_worker_instances():
    redis=FakeRedis();a=RedisControlPlane(redis);b=RedisControlPlane(redis)
    now=200.0
    assert a.consume_budget("w1","rpc",now,2)
    assert b.consume_budget("w1","rpc",now,2)
    assert not a.consume_budget("w1","rpc",now,2)
    assert len(redis.zsets[a._key("budget","w1","rpc")])==2
