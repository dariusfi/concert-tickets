# Setup AWS Lightsail
These instructions have been taken from https://docs.bitnami.com/aws/infrastructure/django/get-started/deploy-django-project/

## Setup ssh key
Download key from AWS conosole. Store in C:\Users\<Name>\.ssh if you're working on Windows. ~/.ssh on Linux. The following instructions assume a deveploment environment on Windows.

Open/Create a file called `config` in the same directory with the following content:
```
Host <aws-lightsail-static-ip>
  IdentityFile C:\Users\<Name>\.ssh\LightsailDefaultKey-eu-central-1.pem
``` 
Open terminal with ssh support and test connection
ssh bitnami@<aws-lightsail-static-ip>

<aws-lightsail-static-ip> is the static IP which is tied to the AWS instance. You can look this up via the AWS console.

## Save Master password
`cat bitnami_application_password`

## Git push to production

This is a convenient way to upload your changes to AWS by simply typing `git push prod` from your local development environment.

After connecting to the AWS server via ssh, create directories for the git repository, and the main project.

```
sudo mkdir /opt/bitnami/projects/ct_git
sudo mkdir /opt/bitnami/projects/ct
sudo chown -R bitnami:bitnami ct_git
sudo chown -R bitnami:bitnami ct
```

Go to this directory, then create a bare git repo:

`git init --bare`

Create file `hooks/post-receive` with the following contents:

```
#!/bin/bash
TARGET="/opt/bitnami/projects/ct"
GIT_DIR="/opt/bitnami/projects/ct_git"

while read oldrev newrev ref
do
    if [ "$ref" = "refs/heads/main" ];
    then
        echo "Deploying to production..."
        git --work-tree="${TARGET}" --git-dir="${GIT_DIR}" checkout -f "main"

        echo "Updating Python dependencies"
        cd ${TARGET}
        source venv/bin/activate

        echo "Using Python version"
        which python
        pip install -r requirements.txt

        echo "Collecting static files"
        python manage.py collectstatic --noinput

        echo "Running migrations"
        python manage.py migrate

        echo "Restarting server"
        sudo /opt/bitnami/ctlscript.sh restart apache
    fi
done

```
Make this file executable:

`chmod +x hooks/post-receive`

Configure git locally to point to this repository:

`git remote add prod ssh://bitnami@<aws-lightsail-static-ip>/opt/bitnami/projects/ct_git`

## Create venv

```
cd /opt/bitnami/projects/ct
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Create Vhost files (Configuration for server)
`cd /opt/bitnami/apache2/conf/vhosts`
Create `ct-vhost.conf` with the following contents, replacing <your-url> with your domain:
```
<IfDefine !IS_CT_LOADED>
  Define IS_CT_LOADED
  WSGIDaemonProcess ct python-home=/opt/bitnami/projects/ct/venv python-path=/opt/bitnami/projects/ct/ processes=2 threads=15
</IfDefine>
<VirtualHost 127.0.0.1:80 _default_:80>
  ServerName <your-url>
  ServerAlias *
  WSGIProcessGroup ct
  Alias /robots.txt /opt/bitnami/projects/ct/static/robots.txt
  Alias /favicon.ico /opt/bitnami/projects/ct/static/favicon.ico
  Alias /static/ /opt/bitnami/projects/ct/static/
  <Directory /opt/bitnami/projects/ct/static>
    Require all granted
  </Directory>
  Alias /media/ /opt/bitnami/projects/ct/media/
  <Directory /opt/bitnami/projects/ct/media>
    Require all granted
  </Directory>
  WSGIScriptAlias / /opt/bitnami/projects/ct/ct/wsgi.py
  <Directory /opt/bitnami/projects/ct/ct>
    <Files wsgi.py>
      Require all granted
    </Files>
  </Directory>
</VirtualHost>
```
And `ct-https-vhost.conf`:
```
<IfDefine !IS_CT_LOADED>
  Define IS_CT_LOADED
  WSGIDaemonProcess ct python-home=/opt/bitnami/projects/ct/venv python-path=/opt/bitnami/projects/ct processes=2 threads=15
</IfDefine>
<VirtualHost 127.0.0.1:443 _default_:443>
  ServerName <your-url>
  ServerAlias *
  SSLEngine on
  SSLCertificateFile "/opt/bitnami/apache/conf/bitnami/certs/server.crt"
  SSLCertificateKeyFile "/opt/bitnami/apache/conf/bitnami/certs/server.key"
  WSGIProcessGroup ct
  Alias /robots.txt /opt/bitnami/projects/ct/static/robots.txt
  Alias /favicon.ico /opt/bitnami/projects/ct/static/favicon.ico
  Alias /static/ /opt/bitnami/projects/ct/static/
  <Directory /opt/bitnami/projects/ct/static>
    Require all granted
  </Directory>
  Alias /media/ /opt/bitnami/projects/ct/media/
  <Directory /opt/bitnami/projects/ct/media>
    Require all granted
  </Directory>
  WSGIScriptAlias / /opt/bitnami/projects/ct/ct/wsgi.py
  <Directory /opt/bitnami/projects/ct/ct>
    <Files wsgi.py>
      Require all granted
    </Files>
  </Directory>
</VirtualHost>
```

Open httpd.conf

`vim /opt/bitnami/apache/conf/httpd.conf`

Add these lines somewhere at the start:

```
SetEnv PYTHONPATH /opt/bitnami/projects/ct:/opt/bitnami/projects/ct/venv/lib/python3.11/site-packages`

# Pass on authorization headers
SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1

```
Replace python3.11 with the Python version you are using.

Restart Apache with

`sudo /opt/bitnami/ctlscript.sh restart apache`

## SSL certificate

For SSL key creation and HTTPS redirection, run the following tool:

`sudo /opt/bitnami/bncert-tool`

This will modify the vhost.conf files above (but will make a backup before). It creates a ssl certificate and sets up a cronjob for regular renewal.

## Create a new database and user

`createuser -U postgres db_user -S -D -R -P`

Enter a new password twice, then the password for the server master account (accessible via AWS Lighsail).

`createdb -U postgres ct -O db_user`

## Create .env file
`vim /opt/bitnami/projects/ct/ct/.env`

Enter the environment variables:
POSTGRES_PASSWORD=...
IS_DEPLOYED=True
EMAIL_PASSWORD=...
SECRET_KEY=...

Fill in the correct values. SECRET_KEY is an arbitrary string, which is used by Django to provide cryptographic signing for various security-related operations.

# Deleting the database
This is useful when migrations are overwritten and all migrations need to be redone. Should not be done once the system is live.

`psql -U postgres`
`DROP DATABASE ct;`

Exit postgres

`\q`

Restart postgres

`createdb -U postgres ct -O db_user`
`sudo /opt/bitnami/ctlscript.sh restart postgresql`

# Follow error log
`sudo tail -f /opt/bitnami/apache2/logs/error_log`
`sudo tail -f /opt/bitnami/apache2/logs/access_log`

Some sort of error log:

`journalctl -xe`
`systemctl status bitnami.service`

# (Re)start all services

`sudo /opt/bitnami/ctlscript.sh start`

Just restart Apache

`sudo /opt/bitnami/ctlscript.sh restart apache`

