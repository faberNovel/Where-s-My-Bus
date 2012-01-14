import os.path
import time
import sys

from fabric.api import *
from fabric.colors import *
from fabric.contrib.console import confirm
from fabric.contrib.files import sed, uncomment, upload_template, append, exists
import wheresmybus.settings as settings_django
import wheresmybus.secrets as secrets

#################
# Configuration #
#################

env.site_name = 'wheresmybus'
env.django_site_name = 'wheresmybus'
env.user = 'wheresmybus'
env.run_daemons_as_user = 'www-data'
env.first_user = 'ubuntu'
env.folder = "/home/{user}/www/{stage}"
env.project_dir = "/home/{user}/www/{stage}/releases/current/{django_site_name}"
env.release = time.strftime('%Y%m%d%H%M%S')

@task
def production():
    """Defines the production stage
    """
    env.stage = 'production'
    env.hosts = [secrets.PRODUCTION_DOMAIN_NAME]
    env.branch = 'master'
    _setup_var()

@task
def staging():
    """Defines the staging stage
    """
    env.stage = 'staging'
    env.hosts = [secrets.STAGING_DOMAIN_NAME]
    env.branch = 'staging'
    _setup_var()

#####################
# End Configuration #
#####################

def _setup_var():
    """Sets the env variables based on the stage
    """
    env.folder = env.folder.format(**env)
    env.project_dir = env.project_dir.format(**env)

# Tomek Kopczuk (www.askthepony.com/blog/): bring 1.0a API up to par
def better_put(local_path, remote_path, mode=None):
    put(local_path.format(**env), remote_path.format(**env), mode)

def parent(path):
    return os.path.abspath(os.path.join(path, ".."))

@task
def ssh():
    require('stage', provided_by=[production, staging])
    local('ssh {user}@{host_string}'.format(**env))

# from http://stackoverflow.com/questions/645363/should-i-use-git-to-deploy-websites
# and http://dvine.de/blog/2010/11/simple-deployment-fabric/
# and https://github.com/tkopczuk/one_second_django_deployment/blob/master/fabfile.py
@task
def deploy():
    """Main deployment routine. Deploys to staging by default.
    """
    require('stage', provided_by=[production, staging])
    
    print green(">>> will deploy branch {branch} to {host_string}").format(**env)
    
    prepare_deploy()
    
    upload_tar_from_git()
    symlink_current_release()
    fetch_requirements()
    
    post_deploy()
    restart_app()
    local('rm -rf build/{release}.tar.gz'.format(**env))

@task
def cleanup():
    # removes all build files
    local('ls build/*')
    if confirm("Will remove all those files. Do you confirm?"):
        local('rm -r build/*')

@task
def prepare_deploy():
    """ Runs the test and make sure everything have been commited
    """
    local("python wheresmybus/manage.py test next")
    with settings(warn_only=True):
        local("git add -p && git commit")
    
def upload_tar_from_git():
    """ Upload an archive of the {branch} branch
    """
    print green('>>> uploading tar from git').format(**env)
    local('git archive --format=tar {branch} | gzip > build/{release}.tar.gz'.format(**env))
    run('mkdir -p {folder}/releases/{release}'.format(**env))
    run('mkdir -p {folder}/packages'.format(**env))
    better_put('build/{release}.tar.gz', '{folder}/packages/'.format(**env))
    run('cd {folder}/releases/{release} && tar zxf ../../packages/{release}.tar.gz'.format(**env))
    
def symlink_current_release():
    """ Symlink the current release.
    """
    print green('>>> updating releases/current to point at {folder}/releases/{release}').format(**env)
    with cd(env.folder):
        with settings(warn_only=True):
            run('rm -f releases/previous')
            run('mv releases/current releases/previous')
        run('ln -s {release} releases/current'.format(**env))

def fetch_requirements():
    print green('>>> updating packages from requirements.txt').format(**env)
    with cd(env.folder):
        sudo('pip install -q -r releases/current/requirements.txt')

def post_deploy():
    print yellow(">>> finishing deployment to {host_string}").format(**env)

    settings_file = os.path.join(env.project_dir, "settings.py")
    sed(settings_file, 'ENV = \"testing\"', 'ENV = \"{stage}\"'.format(**env))
    sed(settings_file, '^PROJECT_DIR.*$', 'PROJECT_DIR = \"{project_dir}\"'.format(**env))

@task
def restart_app():
    stop_app()
    start_app()

@task
def stop_app():
    sudo('supervisorctl stop {site_name}'.format(**env))
    sudo('/etc/init.d/nginx stop')

@task
def start_app():
    sudo('supervisorctl start {site_name}'.format(**env))
    sudo('/etc/init.d/nginx start')

@task
def setup_local():
    if not os.path.exists(settings_django.LOGGING_DIR):
        local("mkdir %s" % settings_django.LOGGING_DIR)
    local("pip install -r requirements.txt")

    with cd(env.django_site_name):
        local("python manage.py syncdb")
        local("python manage.py install_stops")
    
@task
def setup_server():
    """Setups a new server, installing all the required software.
    """
    
    # to use a specific host, do hosts="host1;host2"
    require('hosts', provided_by=[production, staging])
    
    with settings(warn_only=True):
        user_is_configured = local('ssh {user}@{host} echo ""'.format(**env)).succeeded
    
    # Uploading the key and creating the user if necessary
    if not user_is_configured:
        print yellow(">>> user not configured on {host}".format(**env))
        with settings(warn_only=True):
            # copy the key to first user
            local("cat ~/.ssh/id_rsa.pub | ssh -i ~/.ec2/*.pem {first_user}@{host_string} 'mkdir .ssh; cat >> .ssh/authorized_keys'".format(**env))
            # create new user, temporarily giving permissions to first user
            local('ssh {first_user}@{host_string} "sudo useradd -m {user} -s /bin/bash; sudo mkdir -p /home/{user}/.ssh; sudo chown -R {first_user}:{first_user} /home/{user}/"'.format(**env))
            # upload the key
            local('cat ~/.ssh/id_rsa.pub | ssh {first_user}@{host} "cat> /home/{user}/.ssh/authorized_keys"'.format(**env))
            # give back permissions to user
            local('ssh {first_user}@{host_string} "sudo chown -R {user}:{user} /home/{user}/"'.format(**env))
            # add user to the sudoers file
            print red('>>> Connect to your host:')
            print red('$ ssh {first_user}@{host_string}'.format(**env))
            print red(">>> Then add the following line to /etc/sudoers:")
            print red("$ sudo visudo")
            print red("{user} ALL=(ALL) NOPASSWD:ALL".format(**env))
            print red(">>> exiting now")
            sys.exit()
    
    
    print green(">>> updating")
    # Adding mongodb repo
    sudo('apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10')
    append('/etc/apt/sources.list', 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen', use_sudo=True)
    
    sudo("aptitude update")
    sudo("aptitude upgrade")
    
    print green(">>> installing software")
    sudo("aptitude -y install build-essential mercurial python-dev git libxslt-dev libxml2-dev nginx ntp ntpdate webalizer vlogger python-setuptools mongodb-10gen")
    sudo('easy_install pip')
    sudo('pip install supervisor')
    sudo('curl -L https://gist.github.com/raw/1213031/929e578faae2ad3bcb29b03d116bcb09e1932221/supervisord.conf > /etc/init/supervisord.conf')
    
    if not exists('/home/{user}/temp'.format(**env)):
        run('mkdir ~/temp')

    with cd("~/temp"):
        # django-nonrel and djangotoolbox
        for p in ('django-nonrel', 'djangotoolbox'):
            print green(">>> installing "+p)
            if not exists('/home/{user}/temp/'.format(**env)+p):
                run('hg clone http://bitbucket.org/wkornewald/'+p)
            else:
                run('cd %s && hg pull' % p)
            run('cd %s && sudo python setup.py install' % p)
        
        # django-mongodb-engine
        print green(">>> installing django-mongodb-engine")
        if not exists('/home/{user}/temp/mongodb-engine'.format(**env)):
            run('git clone https://github.com/django-mongodb-engine/mongodb-engine')
        else:
            run('cd mongodb-engine && git pull')
        run('cd mongodb-engine && sudo python setup.py install')
    
    update_configuration()

@task
def update_configuration():
    """Update the configuration files on the server
    """
    
    require('stage', provided_by=[production, staging])
    
    print green('>>> uploading configuration files from your templates').format(**env)
    
    upload_template('./conf/supervisord.conf', '/etc/supervisord.conf', use_sudo=True, context=env)
    upload_template('./conf/nginx.conf', '/etc/nginx/sites-available/{site_name}'.format(**env), use_sudo=True, context=env)
    sudo('ln -fs /etc/nginx/sites-available/{site_name} /etc/nginx/sites-enabled/{site_name}'.format(**env))
    
    print green('>>> creating log and sock files')
    sudo('mkdir -p /var/log/wheresmybus/; chown www-data:www-data -R /var/log/wheresmybus')
    sudo('mkdir -p /var/log/supervisord/; chown -R www-data:www-data /var/log/supervisord/')
    sudo('touch /var/run/supervisord.pid; chown www-data:www-data /var/run/supervisord.pid')
    sudo('mkdir -p /var/log/gunicorn/; chown www-data:www-data /var/log/gunicorn/')
    sudo('mkdir -p /var/log/nginx/; chown www-data:www-data /var/log/nginx/')
    
    _cold_restart()

def _cold_restart():
    require('hosts', provided_by=[production, staging])
    
    print green('>>> starting mongodb')
    with settings(warn_only=True):
        sudo('service mongodb stop; service mongodb start')
    
    print green('>>> starting supervisord')
    # to make sure supervisord is not already running
    with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
        sudo('stop supervisord')
    sudo('start supervisord')


