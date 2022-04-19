# Service files

Contains service file templates.
Edit them as necessary (e.g. paths, users etc), then move them to `/etc/systemd/system`.  
Perform a daemon-reload with `systemctl daemon-reload` and then start the service with `systemctl start SERVICENAME`