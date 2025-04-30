# Remote System Info (rsysinfo) 

This is a plugin, systeminfo.py, an INI file to support it, and, systemd service unit. 
I have set this up as a systemd template unit, so that the unit can run as a specific user by enabling 
rsysinf@<user to run as>.service.

You will need to edit rsysinfo.ini, main->domain and cors->origin_url need to be changed. cors is 
important if you're going to use a browser (or javascript in a browser) to access this service otherwise
it can be left alone. The origin_urls are urls that are allowed to refer traffic from. 
Please see the docs under cors for more informatiom.

Once you have edited the ini file you can set up the service with the following steps:

```bash
sudo cp systemctl@ /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable --now rsysinfo@<user to run as>.service
```

If you ran `systemctl enable rsysinfo@mary.service,` the service will use mary as the user to run, 
and locate files based on the home directory of mary. 
