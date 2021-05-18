# ChangeLog

## 0.1

### 0.1.4

- Now use `lua` script.
- **Break change**: You shoud call `FastAPILimiter.init` with `async`.

```python
    await FastAPILimiter.init(redis)
```

### 0.1.3

- Support multiple rate strategy for one route. (#3)

### 0.1.2

- Use milliseconds instead of seconds as default unit of expiration.
- Update default_callback, round milliseconds up to nearest second for `Retry-After` value.
- Access response in the callback.
- Replace transaction with pipeline.

### 0.1.1

- Configuring the global default through the FastAPILimiter.init method.
- Update status to 429 when too many requests.
- Update default_callback params and add `Retry-After` response header.
