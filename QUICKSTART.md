# Quick Start: SystemLink Integration

## ✅ Integration Complete

Your scope/FGEN test harness now supports **NI SystemLink TestMonitor** result publishing.

---

## 🚀 Get Started in 2 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Tests with SystemLink Publishing
```bash
python test_scope_with_fgen.py --publish-to-systemlink
```

---

## 📊 What Happens Next

1. **Tests run normally** (scope captures, FGEN generates)
2. **Results auto-connect to SystemLink** (if server available)
3. **Results appear in SystemLink web UI** under TestMonitor → Results
4. **If SystemLink unavailable** → logs warning, tests continue anyway ✓

---

## 🔗 View Results

After running with `--publish-to-systemlink`:

1. Open **NI SystemLink web interface** (typically `http://localhost:3000`)
2. Navigate to **TestMonitor** → **Results**
3. Filter by program name: `"Scope/FGEN Validation"`
4. Click result to see individual test case measurements

---

## 📚 Documentation

- **Full Guide:** `SYSTEMLINK_INTEGRATION.md`
- **Implementation Details:** `IMPLEMENTATION_SUMMARY.md`
- **API Reference:** SystemLink Python Docs at https://python-docs.systemlink.io/

---

## 🧪 Test Without Hardware

Simulation mode also works with SystemLink:
```bash
# Connects to scope/FGEN in simulation, publishes results to SystemLink
python main.py --self-test

# Or from CLI (if SystemLink unavailable, gracefully continues)
python test_scope_with_fgen.py --publish-to-systemlink
```

---

## ✨ Key Features

✅ **Optional**: Works with or without SystemLink  
✅ **Automatic**: Auto-discovers SystemLink via NI Discovery Service  
✅ **Graceful**: Continues even if SystemLink unavailable  
✅ **Structured**: Results include RMS, frequency limits, pass/fail  
✅ **CLI Flag**: Easy on-demand publishing  
✅ **Quiet**: No spam — only errors/warnings logged  

---

## 🛠️ Advanced Usage

### From Python Code
```python
from test_scope_with_fgen import run_test_suite

failures = run_test_suite(
    scope_resource="Scope1",
    fgen_resource="FGEN1",
    publish_to_systemlink=True,  # ← New parameter
)
```

### Custom SystemLink Host (Future)
```python
from systemlink_reporter import SystemLinkReporter

reporter = SystemLinkReporter(
    logger=logging.getLogger("my_app"),
    host="192.168.1.100",
    port=8080,
)
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'nisystemlink'` | Run `pip install -r requirements.txt` |
| Results not appearing | Check SystemLink server is running; check firewall |
| Lots of warning logs | This is expected if SystemLink unavailable—not an error |
| Connection timeout | Verify SystemLink IP/port; check network connectivity |

---

## 📝 Summary

You can now:

1. ✅ Run tests and publish results to SystemLink TestMonitor
2. ✅ Track test history and trends in SystemLink web UI
3. ✅ Generate reports from centralized test data
4. ✅ Enable/disable publishing with a single CLI flag
5. ✅ Gracefully degrade if SystemLink is unavailable

**All without changing your existing test code!**

---

## 🎯 Next Steps

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify setup: `python test_scope_with_fgen.py --help`
- [ ] Run a test: `python test_scope_with_fgen.py --publish-to-systemlink`
- [ ] View results in SystemLink web UI
- [ ] Read `SYSTEMLINK_INTEGRATION.md` for advanced options

---

Enjoy your centralized test tracking! 🎉

