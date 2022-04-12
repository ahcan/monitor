SYSTEM = {
    'broadcast_time': {
        'TO': 22, 
        'FROM': 6
        }, 
    'HOST': '10.0.200.27', 
    'libery': {
        'FFPROBE': '/usr/local/bin/ffprobe', 
        'FFMPEG': '/usr/local/bin/ffmpeg'
        }, 
    'monitor': {
        'SOURCE': True, 
        'BLACK_SCREEN': True
        }, 
    'BREAK_TIME': 20,
    'RUNNING_BACKUP_QUEUE' : 'running_backup'
    }

API = {
    'master': {
        'ACTIVE': False,
        'URL': '10.0.200.100', 
        'PASSWORD': 'xxxx', 
        'PORT': 8888, 
        'USER': 'monitor'
        },
    'slave': {
        'ACTIVE': True, 
        'URL': '10.0.200.100', 
        'PASSWORD': 'xxxx', 
        'PORT': 8888, 
        'USER': 'monitor'
        }
    }

DATABASE = {
    'master': {
        'NAME': 'monitor', 
        'HOST': '10.0.200.32', 
        'USER': 'MonitorAgent', 
        'ACTIVE': True, 
        'PASSWORD': '11nit0rA93nt', 
        'PORT': 3306
        },
    'slave': {
        'NAME': 'monitor', 
        'HOST': '10.0.200.13', 
        'USER': 'MonitorAgent', 
        'ACTIVE': False, 
        'PASSWORD': '11nit0rA93nt', 
        'PORT': 3306
        }
    }

SUPERVISORD={
    'HOST'                  : 'localhost',
    'PORT'                  : 9001,
    'CONF_DIR'              : '/etc/supervisord/conf.d',
    'CONTROL_DIR'           : '/usr/local/bin/supervisorctl',
    'CONF_TEMPLATE_DIR'     : '/monitor/config/supervisord.template',
    'CONF_EXTENSION'        : '.ini'
    }

SOCKET = {
    "HOST"                  :"10.0.200.99",
    "PORT"                  :5672,
    "USER"                  :"monitor",
    "PASSWD"                :"xxxx"
    }

STIME =['0','0','0']
ETIME = ['6','0','0']
CHANNEL = ['225.1.2.198','225.1.1.131']
