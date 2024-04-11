from enum import Enum


class RateLimitType(Enum):
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"


class LuaScript(Enum):
    FIXED_WINDOW_LIMIT_SCRIPT = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local expire_time = ARGV[2]

        local current = tonumber(redis.call('get', key) or "0")

        if current > 0 then
            if current + 1 > limit then
                return redis.call("PTTL",key)
            else
                redis.call("INCR", key)
                return 0
            end
        else
            redis.call("SET", key, 1, "px", expire_time)
        return 0
        end
    """
    SLIDING_WINDOW_LIMIT_SCRIPT = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local expire_time = tonumber(ARGV[2])
        local current_time = redis.call('TIME')[1]
        local start_time = current_time - expire_time / 1000

        redis.call('ZREMRANGEBYSCORE', key, 0, start_time)

        local current = redis.call('ZCARD', key)
        
        if current >= limit then
            return redis.call("PTTL",key)
        else
            redis.call("ZADD", key, current_time, current_time)
            redis.call('PEXPIRE', key, expire_time)
            return 0
        end
    """
