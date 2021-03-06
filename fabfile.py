# This fabric script tests localwiki on all supported versions of Ubuntu
from fabric.api import *
from vm import *
from ilogue import fexpect


def get_images():
    if settings.EC2_REGION == 'us-west-1':
        images = {
           'ubuntu10.04': 'ami-a1c59de4',
           'ubuntu10.10': 'ami-2b154e6e',
           'ubuntu11.04': 'ami-33fda576',
           'ubuntu11.10': 'ami-0fc59d4a',
           'ubuntu12.04': 'ami-e7712aa2'
        }
    elif settings.EC2_REGION == 'us-west-2':
        images = {
           'ubuntu10.04': 'ami-f6ec60c6',
           'ubuntu10.10': 'ami-7efd714e',
           'ubuntu11.04': 'ami-beef638e',
           'ubuntu11.10': 'ami-a4ec6094',
           'ubuntu12.04': 'ami-38800c08'
        }
    return images


def get_ami(image_name):
    return get_images()[image_name]


prompts = []
prompts += fexpect.expect('3. Paste the API key below:', 'e886fd33ac5743868c31dfebecdb129b')
prompts += fexpect.expect('Would you like to create one now?', 'no')


def test_install_all():
    for image_name in get_images():
        test_install(image_name)


def test_install(image_name):
    with temporary_ec2_instance(ami_id=get_ami(image_name)):
        sudo('apt-get -y install python-software-properties')
        sudo('yes | apt-add-repository ppa:localwikidev/testing')
        sudo('apt-get update')
        with fexpect.expecting(prompts):
            fexpect.sudo('apt-get -y --force-yes install localwiki')
        # On Ubuntu 11.10, downgrade to psycopg2 v2.4.1 or else tests can't run
        # See https://code.djangoproject.com/ticket/16250
        if image_name in ['ubuntu11.10', 'ubuntu12.04']:
            sudo('apt-get -y install python-dev libpq-dev')
            sudo('pip install psycopg2==2.4.1')
        # Give localwiki db user permission to create a database, for tests
        sudo('psql -c "ALTER ROLE localwiki WITH CREATEDB;"', user='postgres')
        sudo('localwiki-manage test pages maps tags versioning diff ckeditor redirects users')

def import_mediawiki(url=None):
    import_prompts = []
    if url:
        import_prompts += fexpect.expect('Enter the address of a MediaWiki site (ex: http://arborwiki.org/):',
                                         url)
    import_prompts += fexpect.expect('Continue import? (yes/no)', 'yes')
    with ec2_instance(ami_id=get_ami('ubuntu10.04')):
        sudo('apt-get -y install python-software-properties')
        sudo('yes | apt-add-repository ppa:localwiki')
        sudo('apt-get update')
        with fexpect.expecting(prompts):
            fexpect.sudo('apt-get -y --force-yes install localwiki')
        with cd('/usr/share/localwiki'):
            sudo('git clone git://github.com/mivanov/localwiki-importers.git')
            with cd('localwiki-importers/mediawiki'):
                sudo('source /usr/share/localwiki/env/bin/activate')
                sudo('pip install -r requirements.txt')
                sudo('deactivate')
                with fexpect.expecting(import_prompts):
                    fexpect.sudo('python import_mediawiki.py')
