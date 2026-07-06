# test-shard

Run pytest shard with coverage.

## Configuration

```jsonc
{
  "command": {
    "test-shard": {
      "template": "Run test shard {shard}",
      "description": "Run pytest shard with coverage",
      "agent": "build"
    }
  }
}
```

## Usage

Invoke the `test-shard` command in a Kilo session.
