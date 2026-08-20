# Installing OpenSSL — Windows, macOS, Ubuntu

Every cert command in this lab (`mcp_install.md`, the walkthrus) needs a working
`openssl`. This guide gets each OS there with the least pain, and calls out the
two classroom classics: **Git Bash path mangling on Windows** and **LibreSSL
masquerading as OpenSSL on macOS**.

## TL;DR

| OS | Fastest working path |
|---|---|
| Windows | Use **Git Bash** (OpenSSL is already inside Git for Windows) — but read the `-subj` gotcha below |
| macOS | `brew install openssl@3` + add it to `PATH` (Apple ships LibreSSL, not OpenSSL) |
| Ubuntu | `sudo apt install openssl` (usually already installed) |

Whatever the OS: finish with the [smoke test](#smoke-test-all-platforms) before class.

---

## Windows

### Option A (recommended for class): Git Bash

If Git for Windows is installed — and for this course it is — **OpenSSL is
already on the machine**. Open **Git Bash** (not PowerShell, not cmd):

```bash
openssl version
# OpenSSL 3.x.x ...
```

> #### ⚠️ The `-subj` gotcha (this is the classroom nightmare)
>
> Git Bash (MSYS) rewrites arguments that start with `/` into Windows paths.
> So `-subj "/CN=mcp-gateway"` silently becomes something like
> `-subj "C:/Program Files/Git/CN=mcp-gateway"` and you get errors such as
> `Subject does not start with '/'` or certs with garbage subjects.
>
> **Fix — either one works:**
>
> ```bash
> # 1. Double the leading slash
> openssl req -x509 -newkey rsa:2048 -nodes \
>   -keyout server.key -out server.crt -days 365 \
>   -subj "//CN=mcp-gateway"
>
> # 2. Or disable path conversion for the command
> MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:2048 -nodes \
>   -keyout server.key -out server.crt -days 365 \
>   -subj "/CN=mcp-gateway"
> ```
>
> PowerShell/cmd users with a native OpenSSL install (Option B) are **not**
> affected — this is purely a Git Bash/MSYS behavior.

### Option B: native install via winget

In PowerShell:

```powershell
winget install --id ShiningLight.OpenSSL.Light --exact
```

- Use the exact ID — a bare `winget install openssl` can match multiple packages.
- `ShiningLight.OpenSSL.LTS.Light` gets the long-term-support 3.5.x line instead
  of the newest series; either is fine for this lab.
- (`FireDaemon.OpenSSL` is a fine alternative package.)

Close and reopen the terminal, then:

```powershell
openssl version
```

If it's not found, the installer's `bin` folder (typically
`C:\Program Files\OpenSSL-Win64\bin`) needs to be added to `PATH`:
Settings → System → About → Advanced system settings → Environment Variables →
edit `Path` → New → paste the folder → OK → **open a new terminal**.

### Option C: WSL

If the student already uses WSL/Ubuntu, just follow the [Ubuntu](#ubuntu)
section inside the WSL shell. Remember files created inside WSL live in the
WSL filesystem — run the *whole* lab (openssl + kubectl) from the same side.

### Windows sanity check

```powershell
where.exe openssl
```

More than one result = PATH conflict. The first entry wins; remove or reorder
if the wrong one is first.

---

## macOS

macOS ships **LibreSSL** under the name `openssl`:

```bash
openssl version
# LibreSSL 3.x.x   <-- not OpenSSL!
```

LibreSSL handles most of this lab, but flags differ from real OpenSSL in places
and error messages won't match the docs. Install the real thing with Homebrew:

```bash
brew install openssl@3
```

Homebrew does **not** put it on `PATH` automatically (it's "keg-only"). Add it:

```bash
# Apple Silicon (M1/M2/M3/M4):
echo 'export PATH="/opt/homebrew/opt/openssl@3/bin:$PATH"' >> ~/.zshrc

# Intel Macs:
echo 'export PATH="/usr/local/opt/openssl@3/bin:$PATH"' >> ~/.zshrc

source ~/.zshrc
```

Verify — it must now say **OpenSSL**, not LibreSSL:

```bash
which openssl     # .../opt/openssl@3/bin/openssl
openssl version   # OpenSSL 3.x.x
```

No Homebrew? Install it first: [brew.sh](https://brew.sh), or accept LibreSSL
for this lab — the commands in `mcp_install.md` work on current LibreSSL too.

---

## Ubuntu

Usually already installed. If not, or to update:

```bash
sudo apt update
sudo apt install -y openssl
openssl version
# OpenSSL 3.x.x
```

That's it. (This is why the demo machine runs Ubuntu.)

---

## Smoke test (all platforms)

Run this before class — it exercises exactly what the lab needs (a CA, a CSR,
and a signed cert). Takes ~5 seconds:

```bash
mkdir -p /tmp/ssl-test && cd /tmp/ssl-test

# 1. Make a CA
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout test-ca.key -out test-ca.crt -days 1 \
  -subj "/CN=test-ca"

# 2. Make a key + CSR
openssl req -newkey rsa:2048 -nodes \
  -keyout test.key -out test.csr \
  -subj "/CN=test-client"

# 3. Sign the CSR with the CA
openssl x509 -req -in test.csr \
  -CA test-ca.crt -CAkey test-ca.key -CAcreateserial \
  -out test.crt -days 1

# 4. Verify the chain
openssl verify -CAfile test-ca.crt test.crt
# expected: test.crt: OK
```

> Windows Git Bash users: remember `//CN=...` or the `MSYS_NO_PATHCONV=1` prefix.

If step 4 prints `test.crt: OK`, the student is ready for the lab.

---

## Troubleshooting quick reference

| Symptom | Platform | Fix |
|---|---|---|
| `Subject does not start with '/'` or weird `C:/Program Files/...` in cert subject | Windows Git Bash | Use `//CN=...` or prefix `MSYS_NO_PATHCONV=1` |
| `openssl: command not found` after install | Windows | Open a **new** terminal; check `PATH` includes the OpenSSL `bin` folder (`where.exe openssl`) |
| `openssl version` says LibreSSL | macOS | `brew install openssl@3` and fix `PATH` (see macOS section) |
| `which openssl` still shows `/usr/bin/openssl` after brew install | macOS | The `PATH` export didn't load — `source ~/.zshrc`, or the export went to the wrong shell profile |
| Two different `openssl` in `where.exe`/`which -a` | any | First entry on `PATH` wins — remove/reorder |
| Permission errors writing keys | any | Don't work in a system directory; use your home dir or `/tmp` |
