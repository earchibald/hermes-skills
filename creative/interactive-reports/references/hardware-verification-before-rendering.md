# Hardware Verification Before Rendering

Before building an interactive report that depends on machine specs
(architecture diagrams, resource estimates, deployment targets), SSH into
the actual hosts and collect real data. Assumptions about hardware are
often wrong and waste token rounds.

## Commands

```bash
# CPU model + cores
ssh <host> "cat /proc/cpuinfo | grep 'model name' | head -1 && nproc"

# RAM
ssh <host> "free -h | grep Mem"

# Disk
ssh <host> "df -h / | tail -1"

# OS
ssh <host> "cat /etc/os-release | head -3"
```

For macOS hosts:

```bash
ssh <host> "sysctl -n hw.model && sysctl -n hw.memsize && df -h / | tail -1"
```

## Pitfalls

- **Verify SSH key is deployed before assuming an error.** If `ssh <host>` says
  "Host key verification failed," the key hasn't been added to that host's
  authorized_keys or known_hosts.
- **Don't assume machine power** based on form factor (NUC, Mini, Air).
  NUC-1 had an i3-6100U with 31GB RAM. NUC-2/3 had Intel N95 with 7.5GB.
  The M1 Mini was an 8GB machine with limited disk. Measure, don't guess.
- **Check running services too.** NUC-1 looked like it had 21GB free, but
  ClickHouse was using 18.7% CPU continuously — the CPU was the constraint,
  not RAM. Always run `ps aux --sort=-%mem | head -10` to see what's loaded.
- **RAM usage ≠ capacity.** 9.6GB in use on a 31GB machine means 21GB free.
  But if that 9.6GB includes a VirtualBox VM + k8s + ClickHouse, the machine
  is already working. Ask whether the machine has headroom for another daemon.
- **APFS df output lies.** On macOS, `df -h` can show confusing numbers due to
  snapshots and purgeable space. Cross-check with `diskutil info /`.
