Terraformer
===========

Currently there's just the one Terraformer script, to create a new WordPress site.

1. Copy conf/wordpress.json.sample to conf/wordpress.json and tweak the settings to suit your environment
2. Run `sudo python terra.py wordpress` (running as super-user allows the script to reload Apache for you)
3. Follow the console prompts

In an ideal world, it'll better handle the Apache restart thing, or make it optional. At the moment I just made this
for my setup, so I might put that into the conf file as a "post-run command" type setting.

Changelog
---------

Version 0.2:
- Added Django as a skeleton
- Added mixiins for common tasks like creating MySQL databases, generating passwords and downloading files
- Added logging
- Abstracted Apache restart to "prerun" and "postrun" commands, that can be specified in the skeleton conf file

Version 0.1:
- Initial commit