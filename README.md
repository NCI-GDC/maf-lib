# Git Templates
Git templates that can be used as git configuration template for gdc projects. 

## Available configs
- Git hooks
  - security scanning pre-commit hook: Check possible sensitive information that's in newly added code or filenames. If you think the detected line is a false positive. You can run it as `git commit -n` to skip it.
  - commit-message hook according to [angular guidelines](https://docs.google.com/document/d/1QrDFcIiPjSLDn3EL15IJygNPiHORgU1_OOAqWjiDU5Y/edit#).


## Setup git templates
- Clone this directory, then run `git config --global init.templatedir $template_dir`. Afterward new repositories will use this directory for templates.
- For existing directory, run  `git init --template $template_dir` to reinitiate it.


## Contributing

Read how to contribute [here](https://github.com/NCI-GDC/gdcapi/blob/master/CONTRIBUTING.md)
