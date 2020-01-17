### openconnect-okta-helper

```
brew install openconnect AlJohri/-/openconnect-okta-helper
```

Replace `<USERNAME>` with your Okta username. Run `openconnect-okta-helper --help` for more options.

WaPo Main VPN
```bash
sudo openconnect \
	--background \
	--pid-file="$HOME/.mainvpn.pid" \
    --protocol=nc \
    --user=<USERNAME> \
    --cookie="$(openconnect-okta-helper \
    	--protocol nc \
    	--gateway ra.washpost.com \
    	--okta-domain washpost.okta.com \
    	--username <USERNAME>)" \
    --authgroup=TWP-main \
    -vv \
    ra.washpost.com &> "$HOME/.mainvpn.log"
```

WaPo Arc VPN
```bash
sudo openconnect \
	--background \
    --protocol=anyconnect \
    --pid-file="$HOME/.arcvpn.pid" \
    --user=<USERNAME> \
    --cookie="$(openconnect-okta-helper \
    	--protocol anyconnect \
    	--gateway ra.network.aws.arc.pub \
    	--okta-domain washpost.okta.com \
    	--okta-group ARC_OKTA_USERS \
    	--username <USERNAME>)" \
    -vv \
    ra.network.aws.arc.pub &> "$HOME/.arcvpn.log"
```

Check Running VPN
```bash
ps aux | grep openconnect
tail -f "$HOME/.mainvpn.log"
```

Stop VPN
```bash
sudo pkill -2 -F "$HOME/.mainvpn.pid"
```

Prevent Password Prompt for `sudo` when using VPN
```bash
sudo sh -c 'echo "%admin ALL=(ALL) NOPASSWD: /usr/local/bin/openconnect, /bin/kill" > /etc/sudoers.d/openconnect'
```
