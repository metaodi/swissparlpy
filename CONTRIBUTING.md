# Contributing

If you want to participate in this project, please follow this guidline.

Fork and clone this repository:

```bash
git clone git@github.com:your-username/swissparlpy.git
```

Install the dependencies using `flit`:

```bash
pip install flit
flit install -s
```

Make sure the tests pass:

```bash
pytest
```

To ensure a good quality of the code use `flake8` to check the code style:

```bash
flake8 --install-hook git
```

## Create a pull request

1. Choose the `develop` branch as a target for new/changed functionality, `main` should only be targeted for urgent bugfixes.
2. While it's not strictly required, it's highly recommended to create a new branch on your fork for each pull request.
3. Push to your fork and [submit a pull request][pr].
4. Check if the [build ran successfully][ci] and try to improve your code if not.

At this point you're waiting for my review.
I might suggest some changes or improvements or alternatives.

Some things that will increase the chance that your pull request is accepted:

* Write tests.
* Follow the Python style guide ([PEP-8][pep8]).
* Write a [good commit message][commit].

[pr]: https://github.com/metaodi/swissparlpy/compare/
[ci]: https://github.com/metaodi/swissparlpy/actions
[pep8]: https://www.python.org/dev/peps/pep-0008/
[commit]: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
