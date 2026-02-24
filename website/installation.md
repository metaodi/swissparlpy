---
title: Installation
layout: default
nav_order: 2
---

# Installation
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Requirements

swissparlpy requires **Python 3.9 or higher**.

---

## Install from PyPI

swissparlpy is available on [PyPI](https://pypi.org/project/swissparlpy/). Install it with pip:

```bash
pip install swissparlpy
```

---

## Install with Visualization Support

To enable the [voting visualization feature](usage#visualize-voting-results), install with the `visualization` extra:

```bash
pip install swissparlpy[visualization]
```

This installs additional dependencies (`matplotlib`, `Pillow`) needed for plotting seat maps.

---

## Development Installation

To develop on this project, first install [uv](https://github.com/astral-sh/uv):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then clone the repository and install the package in editable mode with all development dependencies:

```bash
git clone https://github.com/metaodi/swissparlpy.git
cd swissparlpy
uv pip install -e ".[dev,test,visualization]"
```

Alternatively, use the provided setup script:

```bash
./dev_setup.sh
```

---

## Verify Installation

After installation, verify it works:

```python
import swissparlpy as spp
print(spp.__version__)
tables = spp.get_tables()
print(tables[:3])
```
